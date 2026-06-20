"""
AI 教练引擎 v2.0 —— 信号处理管线 + 特征提取 + 评分诊断
升级内容：
  1. 巴特沃斯带通滤波（去除重力+高频噪声）
  2. 击发时刻检测（Jerk 峰值检测算法）
  3. 扳机曲线分析（击发前加速度平滑度）
  4. 枪口跳动模型（击发后角速度积分→枪口偏移轨迹）
  5. 频域特征（主频率、频谱质心）
  6. 图表数据自动生成（扳机曲线、枪口轨迹、分数曲线）
"""
import statistics
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import signal as scipy_signal
from scipy import integrate


# ============================================================
# 信号处理层
# ============================================================

class SignalProcessor:
    """IMU 信号预处理管线：去直流 → 带通滤波 → 归一化"""

    @staticmethod
    def remove_dc(signal: np.ndarray) -> np.ndarray:
        """去除直流偏置（重力分量），保留动态运动信息"""
        return signal - np.mean(signal, axis=0)

    @staticmethod
    def butter_bandpass(data: np.ndarray, lowcut: float = 1.0,
                        highcut: float = 80.0, fs: int = 400, order: int = 4):
        """
        巴特沃斯带通滤波
        - 1Hz 高通：滤除重力加速度（DC ~ 0Hz）和极低频漂移
        - 80Hz 低通：滤除传感器高频噪声，保留人体动作频段
        """
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = scipy_signal.butter(order, [low, high], btype='band')
        return scipy_signal.filtfilt(b, a, data, axis=0)

    @staticmethod
    def normalize(data: np.ndarray) -> np.ndarray:
        """Z-score 归一化 —— 消除不同传感器灵敏度差异"""
        std = np.std(data, axis=0)
        std[std == 0] = 1e-10
        return (data - np.mean(data, axis=0)) / std

    @classmethod
    def preprocess(cls, accel: np.ndarray, gyro: np.ndarray, fs: int = 400):
        """完整预处理管线：去直流 → 带通滤波（短数据自动降级）"""
        accel = cls.remove_dc(accel)
        gyro = cls.remove_dc(gyro)

        # 巴特沃斯 4 阶 filtfilt 需要 padlen=27 个点，短数据跳过滤波
        min_len = 30
        if len(accel) >= min_len:
            accel = cls.butter_bandpass(accel, lowcut=1.0, highcut=80.0, fs=fs)
        if len(gyro) >= min_len:
            gyro = cls.butter_bandpass(gyro, lowcut=1.0, highcut=60.0, fs=fs)

        return accel, gyro


# ============================================================
# 击发时刻检测
# ============================================================

class ShotDetector:
    """检测击发时刻 —— 在加速度 Jerk 信号中寻找峰值"""

    @staticmethod
    def jerk_magnitude(accel: np.ndarray, fs: int = 400) -> np.ndarray:
        """计算 Jerk（加加速度）的模长 —— 反映加速度变化的剧烈程度"""
        dt = 1.0 / fs
        jerk = np.diff(accel, axis=0) / dt
        return np.linalg.norm(jerk, axis=1)

    @staticmethod
    def detect(accel: np.ndarray, gyro: np.ndarray, fs: int = 400) -> int:
        """
        检测击发时刻索引
        原理：扣扳机击发瞬间，加速度出现剧烈突变（Jerk 峰值）
        """
        jerk_mag = ShotDetector.jerk_magnitude(accel, fs)
        threshold = np.mean(jerk_mag) + 2.0 * np.std(jerk_mag)

        peaks, properties = scipy_signal.find_peaks(
            jerk_mag,
            height=threshold,
            distance=max(8, fs // 50)
        )

        if len(peaks) == 0:
            # fallback：用 Jerk 最大点
            return int(np.argmax(jerk_mag))
        # 取最高的峰值
        best = peaks[np.argmax(properties['peak_heights'])]
        return int(best)

    @staticmethod
    def split_windows(accel: np.ndarray, gyro: np.ndarray,
                      trigger_idx: int, pre_ms: int = 200,
                      post_ms: int = 100, fs: int = 400) -> dict:
        """按击发时刻切分时间窗"""
        pre_n = int(pre_ms / 1000 * fs)
        post_n = int(post_ms / 1000 * fs)
        start = max(0, trigger_idx - pre_n)
        end = min(len(accel), trigger_idx + post_n)
        return {
            'trigger_idx': trigger_idx,
            'pre_accel': accel[start:trigger_idx],
            'post_accel': accel[trigger_idx:end],
            'pre_gyro': gyro[start:trigger_idx],
            'post_gyro': gyro[trigger_idx:end],
        }


# ============================================================
# 特征提取
# ============================================================

class FeatureExtractor:
    """从 IMU 信号中提取有物理意义的特征"""

    @staticmethod
    def rms(signal: np.ndarray) -> float:
        """均方根幅值"""
        return float(np.sqrt(np.mean(np.square(signal))))

    @staticmethod
    def peak_to_peak(signal: np.ndarray) -> float:
        """峰-峰值"""
        return float(np.ptp(signal))

    @staticmethod
    def jerk_energy(accel: np.ndarray, fs: int = 400) -> float:
        """Jerk 信号总能量 —— 衡量动作剧烈程度"""
        dt = 1.0 / fs
        jerk = np.diff(accel, axis=0) / dt
        return float(np.sum(np.square(np.linalg.norm(jerk, axis=1))))

    @staticmethod
    def dominant_frequency(signal: np.ndarray, fs: int = 400) -> float:
        """主频率 —— FFT 中能量最高的频率分量"""
        n = len(signal)
        if n < 4:
            return 0.0
        freqs = np.fft.rfftfreq(n, 1 / fs)
        spectrum = np.abs(np.fft.rfft(signal, axis=0))
        mag = np.linalg.norm(spectrum, axis=1)
        idx = int(np.argmax(mag))
        return float(freqs[idx])

    @staticmethod
    def spectral_centroid(signal: np.ndarray, fs: int = 400) -> float:
        """频谱质心 —— 能量分布的加权平均频率"""
        n = len(signal)
        if n < 4:
            return 0.0
        freqs = np.fft.rfftfreq(n, 1 / fs)
        spectrum = np.abs(np.fft.rfft(signal, axis=0))
        mag = np.linalg.norm(spectrum, axis=1)
        total = np.sum(mag)
        if total == 0:
            return 0.0
        return float(np.sum(freqs * mag) / total)

    @staticmethod
    def trigger_smoothness(pre_accel: np.ndarray, fs: int = 400) -> float:
        """
        扳机平滑度 (0-100)
        扣扳机过程中加速度越平稳 → 分越高；波动大 → "抢火"或"猛扣"
        """
        if len(pre_accel) < 3:
            return 50.0
        mag = np.linalg.norm(pre_accel, axis=1)
        # 一阶差分（幅值变化率）
        jitter = np.mean(np.abs(np.diff(mag)))
        score = max(0, 100 - jitter * 80)
        return round(min(100, float(score)), 2)

    @staticmethod
    def muzzle_displacement(post_gyro: np.ndarray, fs: int = 400) -> np.ndarray:
        """
        角速度积分 → 枪口角度位移（仅 pitch/yaw 两轴）
        单位化为度，简化模型
        """
        dt = 1.0 / fs
        # 角速度单位假设为 rad/s
        angles = integrate.cumulative_trapezoid(post_gyro[:, :2], dx=dt, axis=0, initial=0)
        return np.degrees(angles)  # 转为度

    @staticmethod
    def trigger_curve_points(pre_accel: np.ndarray, max_points: int = 50) -> list:
        """提取扳机曲线（加速度幅值序列），降采样到适合前端绘图"""
        if len(pre_accel) < 2:
            return []
        mag = np.linalg.norm(pre_accel, axis=1)
        if len(mag) > max_points:
            idx = np.linspace(0, len(mag) - 1, max_points, dtype=int)
            mag = mag[idx]
        # 归一化到 [0, 1]
        amax, amin = np.max(mag), np.min(mag)
        if amax > amin + 1e-10:
            mag = (mag - amin) / (amax - amin)
        return [round(float(v), 4) for v in mag]

    @staticmethod
    def muzzle_trajectory_points(post_gyro: np.ndarray,
                                 fs: int = 400, max_points: int = 50) -> list:
        """枪口轨迹点序列（pitch, yaw 角度对），降采样到适合前端绘图"""
        displacement = FeatureExtractor.muzzle_displacement(post_gyro, fs)
        if len(displacement) < 2:
            return []
        if len(displacement) > max_points:
            idx = np.linspace(0, len(displacement) - 1, max_points, dtype=int)
            displacement = displacement[idx]
        return [[round(float(p), 4), round(float(y), 4)]
                for p, y in displacement]


# ============================================================
# 数据结构
# ============================================================

@dataclass
class ScoreBreakdown:
    trigger_control: float
    stability: float
    follow_through: float
    consistency: float
    total: float
    per_shot_details: list = field(default_factory=list)


# ============================================================
# AI 教练核心引擎 v2.0
# ============================================================

class AIEngine:
    """AI 教练核心引擎 —— 完整信号处理 + 评分诊断管线"""

    FS = 400  # IMU 采样率 (Hz)

    # ---- F1: 动作评分 ----

    def compute_motion_score(self, shots) -> ScoreBreakdown:
        """
        动作评分（升级版）
        每枪管线：预处理 → 击发检测 → 切窗 → 特征提取 → 维度评分
        """
        if not shots:
            return ScoreBreakdown(0, 0, 0, 0, 0)

        trigger_list, stability_list, follow_list = [], [], []
        per_shot = []

        for shot in shots:
            imu = shot.get('imu_data', {})
            if not imu:
                continue
            accel_raw = np.array(imu.get('accel', []), dtype=np.float64)
            gyro_raw = np.array(imu.get('gyro', []), dtype=np.float64)
            if accel_raw.ndim != 2 or accel_raw.shape[0] < 5:
                continue
            if gyro_raw.ndim != 2 or gyro_raw.shape[0] < 5:
                continue

            # 1) 信号预处理
            accel, gyro = SignalProcessor.preprocess(accel_raw, gyro_raw, fs=self.FS)

            # 2) 击发时刻检测
            trigger_idx = ShotDetector.detect(accel, gyro, fs=self.FS)
            windows = ShotDetector.split_windows(accel, gyro, trigger_idx, fs=self.FS)

            pre_a = windows['pre_accel']
            post_a = windows['post_accel']
            post_g = windows['post_gyro']

            # 3) 特征提取 → 评分
            smoothness = FeatureExtractor.trigger_smoothness(pre_a, fs=self.FS) if len(pre_a) > 0 else 50
            jerk_e = FeatureExtractor.jerk_energy(pre_a, fs=self.FS) if len(pre_a) > 2 else 0
            trigger_score = self._calc_trigger_score(smoothness, jerk_e)

            stab_rms = FeatureExtractor.rms(np.std(pre_a, axis=0)) if len(pre_a) > 0 else 1.0
            stability_score = self._calc_stability_score(stab_rms)

            if len(post_a) > 0:
                ft_rms = FeatureExtractor.rms(np.std(post_a, axis=0))
                muzzle_traj = FeatureExtractor.muzzle_displacement(post_g, fs=self.FS)
                muzzle_disp = float(np.max(np.abs(muzzle_traj))) if len(muzzle_traj) > 0 else 0.0
            else:
                ft_rms, muzzle_disp = 0.0, 0.0
            follow_score = self._calc_follow_through_score(ft_rms, muzzle_disp)

            # 4) 图表数据
            trigger_curve = FeatureExtractor.trigger_curve_points(pre_a)
            mz_points = FeatureExtractor.muzzle_trajectory_points(post_g, fs=self.FS)

            trigger_list.append(trigger_score)
            stability_list.append(stability_score)
            follow_list.append(follow_score)
            per_shot.append({
                'shot_number': shot.get('shot_number', 0),
                'trigger_control': trigger_score,
                'stability': stability_score,
                'follow_through': follow_score,
                'trigger_curve': trigger_curve,
                'muzzle_trajectory': mz_points,
                'trigger_idx': trigger_idx,
                'dominant_freq': round(
                    FeatureExtractor.dominant_frequency(pre_a, fs=self.FS)
                    if len(pre_a) > 4 else 0.0, 2),
            })

        avg_trigger = statistics.mean(trigger_list) if trigger_list else 0
        avg_stability = statistics.mean(stability_list) if stability_list else 0
        avg_follow = statistics.mean(follow_list) if follow_list else 0
        avg_consistency = self._score_consistency(trigger_list, stability_list, follow_list)

        total = (avg_trigger * 0.30 + avg_stability * 0.30 +
                 avg_follow * 0.25 + avg_consistency * 0.15)
        return ScoreBreakdown(
            round(avg_trigger, 2), round(avg_stability, 2),
            round(avg_follow, 2), round(avg_consistency, 2),
            round(total, 2), per_shot,
        )

    def _calc_trigger_score(self, smoothness: float, jerk_energy: float) -> float:
        """扳机控制评分 = 平滑度(70%) + Jerk 能量惩罚(30%)"""
        jerk_penalty = min(50, jerk_energy * 0.08)
        score = smoothness * 0.7 + (100 - jerk_penalty) * 0.3
        return round(max(0, min(100, score)), 2)

    def _calc_stability_score(self, stability_rms: float) -> float:
        """握持稳定性评分 —— RMS 越小越稳"""
        score = max(0, 100 - stability_rms * 6)
        return round(min(100, score), 2)

    def _calc_follow_through_score(self, ft_rms: float, muzzle_disp: float) -> float:
        """跟进控制 = 稳定性(60%) + 枪口位移(40%)"""
        stab_part = max(0, 100 - ft_rms * 8)
        muzzle_part = max(0, 100 - muzzle_disp * 30)
        score = stab_part * 0.6 + muzzle_part * 0.4
        return round(max(0, min(100, score)), 2)

    # ---- F1: 准度评分 ----

    def compute_accuracy_score(self, shots) -> dict:
        """准度评分 = 0.45*RingScore + 0.35*GroupScore + 0.20*OffsetScore"""
        hit_points, ring_scores = [], []
        for shot in shots:
            hx, hy, ring = shot.get('hit_x'), shot.get('hit_y'), shot.get('hit_ring')
            if hx is not None and hy is not None:
                hit_points.append((hx, hy))
            if ring is not None:
                ring_scores.append(ring)

        mean_ring = statistics.mean(ring_scores) if ring_scores else 0
        group_radius = self._compute_group_radius(hit_points)
        center_offset = self._compute_center_offset(hit_points)
        ring_score = min(100, mean_ring * 10)
        group_score = max(0, 100 - group_radius * 0.5)
        offset_score = max(0, 100 - center_offset * 2)
        total = 0.45 * ring_score + 0.35 * group_score + 0.20 * offset_score

        return {
            'mean_ring': mean_ring, 'group_radius': group_radius,
            'center_offset': center_offset, 'ring_score': round(ring_score, 2),
            'group_score': round(group_score, 2), 'offset_score': round(offset_score, 2),
            'total_score': round(total, 2),
        }

    def compute_overall(self, motion_total: float, accuracy_total: float,
                        neutral_penalty: float = 0, motion_weight: float = 0.5) -> dict:
        total = motion_weight * motion_total + (1 - motion_weight) * accuracy_total - neutral_penalty
        return {'motion_weight': motion_weight, 'accuracy_weight': 1 - motion_weight,
                'total_score': round(max(0, total), 2)}

    # ---- F2: 诊断 ----

    def diagnose_issues(self, motion_breakdown: ScoreBreakdown) -> list[dict]:
        """基于评分维度和特征 诊断 Top 1-3 问题"""
        issues = []
        if motion_breakdown.trigger_control < 60:
            issues.append({
                'label': 'Trigger_Jerk',
                'severity': 'high' if motion_breakdown.trigger_control < 40 else 'medium',
                'description': '扣扳机时出现突然发力，导致枪口偏移',
            })
        if motion_breakdown.stability < 60:
            issues.append({
                'label': 'Grip_Instability',
                'severity': 'high' if motion_breakdown.stability < 40 else 'medium',
                'description': '握持稳定性不足，瞄准点漂移过大',
            })
        if motion_breakdown.follow_through < 60:
            issues.append({
                'label': 'Poor_Follow_Through',
                'severity': 'high' if motion_breakdown.follow_through < 40 else 'medium',
                'description': '击发后缺乏跟进控制，枪口位移过大，影响下一枪准备',
            })
        if motion_breakdown.consistency < 60:
            issues.append({
                'label': 'Anticipation',
                'severity': 'medium',
                'description': '各枪之间动作一致性不足，可能存在预判性动作，肌肉记忆尚未形成',
            })
        return issues[:3]

    # ---- F3: 建议 ----

    DRILL_LIBRARY = {
        'Trigger_Jerk': {
            'drill': 'Dry Fire Wall Drill',
            'description': '面对白墙，在空枪状态下慢速扣扳机，感受二道火的阻力点，关注准星是否在扣发过程中保持不动',
            'reps': '50次/组 x 3组', 'duration_minutes': 15,
            'success_criteria': '扣发过程中瞄准点位移 < 5mm',
        },
        'Grip_Instability': {
            'drill': 'Grip Pressure Drill',
            'description': '以70%握力持枪，保持瞄准点稳定15秒。逐步增加持续时间到30秒',
            'reps': '30次/组 x 3组', 'duration_minutes': 10,
            'success_criteria': '15秒内瞄准点偏移半径 < 8mm',
        },
        'Poor_Follow_Through': {
            'drill': 'Follow-Through Hold Drill',
            'description': '击发后保持扳机在最后位置2秒，感受枪口回复到瞄准位置的过程，再缓慢释放扳机',
            'reps': '30次/组 x 2组', 'duration_minutes': 10,
            'success_criteria': '击发后2秒内枪口位移 < 3mm',
        },
        'Anticipation': {
            'drill': 'Ball & Dummy Drill',
            'description': '混合实弹与空弹（由教练或随机装填），消除对后坐力的预判习惯',
            'reps': '20发混合 x 2组', 'duration_minutes': 15,
            'success_criteria': '空弹时枪口无明显下压动作',
        },
    }

    def generate_recommendations(self, issues: list[dict]) -> list[dict]:
        recommendations = []
        for issue in issues:
            label = issue['label']
            if label in self.DRILL_LIBRARY:
                d = self.DRILL_LIBRARY[label]
                recommendations.append({
                    'issue': label, 'drill': d['drill'],
                    'description': d['description'], 'reps': d['reps'],
                    'duration_minutes': d['duration_minutes'],
                    'success_criteria': d['success_criteria'],
                })
        return recommendations[:3]

    # ---- F4: 水平评估 ----

    def update_skill_rating(self, user_id: str, motion_score: float, accuracy_score: float,
                            current_rating: Optional[dict] = None) -> dict:
        alpha = 0.3
        prev_motion = current_rating.get('ema_motion_score', motion_score) if current_rating else motion_score
        prev_accuracy = current_rating.get('ema_accuracy_score', accuracy_score) if current_rating else accuracy_score
        prev_count = current_rating.get('total_sessions_analyzed', 0) if current_rating else 0

        new_motion = alpha * motion_score + (1 - alpha) * prev_motion
        new_accuracy = alpha * accuracy_score + (1 - alpha) * prev_accuracy
        new_count = prev_count + 1

        if new_count < 5:
            level = 'L1'
        else:
            combined = new_motion * 0.6 + new_accuracy * 0.4
            if combined >= 85:
                level = 'L5'
            elif combined >= 75:
                level = 'L4'
            elif combined >= 60:
                level = 'L3'
            elif combined >= 45:
                level = 'L2'
            else:
                level = 'L1'

        return {
            'current_level': level, 'ema_motion_score': round(new_motion, 2),
            'ema_accuracy_score': round(new_accuracy, 2), 'total_sessions_analyzed': new_count,
        }

    # ---- F5: 训练计划 ----

    def generate_training_plan(self, user_profile: dict, issues: list[dict]) -> list[dict]:
        frequency = user_profile.get('training_frequency', 3)
        session_minutes = user_profile.get('session_duration_minutes', 30)
        weeks = user_profile.get('plan_weeks', 1)

        daily_plans = []
        total_days = weeks * 7
        for day in range(total_days):
            is_training_day = (day % max(1, 7 // frequency) == 0)
            if is_training_day:
                drills = []
                if issues:
                    primary = issues[0]['label']
                    drill = self.DRILL_LIBRARY.get(primary, self.DRILL_LIBRARY['Trigger_Jerk'])
                    drills.append({
                        'drill': drill['drill'],
                        'duration_minutes': min(drill['duration_minutes'], session_minutes // 3),
                    })
                daily_plans.append({
                    'day': day + 1, 'is_training': True, 'drills': drills,
                    'total_minutes': sum(d['duration_minutes'] for d in drills),
                })
            else:
                daily_plans.append({'day': day + 1, 'is_training': False, 'note': '休息日'})
        return daily_plans

    # ---- 聚合查询 ----

    def get_aggregated_result(self, session_id: str) -> Optional[dict]:
        from apps.training.models import TrainingSession
        from .models import MotionScore, AccuracyScore, OverallScore, IssueDiagnosis, Recommendation, SkillRating
        try:
            session = TrainingSession.objects.select_related('result').get(id=session_id)
        except TrainingSession.DoesNotExist:
            return None

        result = {
            'session_id': str(session.id),
            'total_shots': session.total_shots,
            'duration_seconds': session.duration_seconds,
            'avg_ring': session.result.avg_ring if hasattr(session, 'result') else None,
            'scatter_data': session.result.scatter_data if hasattr(session, 'result') else [],
            'score_curve': session.result.score_curve if hasattr(session, 'result') else [],
            'motion_data': session.result.motion_data if hasattr(session, 'result') else [],
        }

        for model, key in [
            (MotionScore, 'motion_score'), (AccuracyScore, 'accuracy_score'),
            (OverallScore, 'overall_score'), (IssueDiagnosis, 'diagnosis'),
            (Recommendation, 'recommendation'),
        ]:
            try:
                obj = model.objects.get(session=session)
                data = {}
                for f in model._meta.fields:
                    if f.name not in ['id', 'session']:
                        data[f.name] = getattr(obj, f.name)
                result[key] = data
            except model.DoesNotExist:
                result[key] = None

        return result

    # ---- 完整流水线 ----

    def run_full_pipeline(self, session_id: str) -> str:
        """完整 AI 分析流水线"""
        from apps.training.models import TrainingSession, TrainingResult
        from .models import (MotionScore, AccuracyScore, NeutralPenalty, OverallScore,
                             IssueDiagnosis, Recommendation, SkillRating)
        try:
            session = TrainingSession.objects.get(id=session_id)
        except TrainingSession.DoesNotExist:
            return 'session_not_found'

        shots = list(session.shots.values())
        if len(shots) < 10:
            return 'insufficient_shots'

        # F1: 评分
        motion = self.compute_motion_score(shots)
        accuracy = self.compute_accuracy_score(shots)
        overall = self.compute_overall(motion.total, accuracy['total_score'])

        # 保存 MotionScore（含 per_shot_details）
        MotionScore.objects.update_or_create(
            session=session, defaults={
                'trigger_control': motion.trigger_control,
                'stability': motion.stability,
                'follow_through': motion.follow_through,
                'consistency': motion.consistency,
                'total_score': motion.total,
                'details': {'per_shot': motion.per_shot_details},
            },
        )
        AccuracyScore.objects.update_or_create(session=session, defaults=accuracy)
        NeutralPenalty.objects.get_or_create(session=session, defaults={'total_penalty': 0})
        OverallScore.objects.update_or_create(session=session, defaults=overall)

        # F2: 诊断
        issues = self.diagnose_issues(motion)
        IssueDiagnosis.objects.update_or_create(session=session, defaults={'issues': issues})

        # F3: 建议
        recommendations = self.generate_recommendations(issues)
        Recommendation.objects.update_or_create(session=session, defaults={'items': recommendations})

        # F4: 水平评估
        try:
            rating = SkillRating.objects.get(user=session.user)
            updated = self.update_skill_rating(
                str(session.user.id), motion.total, accuracy['total_score'],
                {'ema_motion_score': rating.ema_motion_score,
                 'ema_accuracy_score': rating.ema_accuracy_score,
                 'total_sessions_analyzed': rating.total_sessions_analyzed},
            )
            for k, v in updated.items():
                setattr(rating, k, v)
            rating.save()
        except SkillRating.DoesNotExist:
            SkillRating.objects.create(
                user=session.user, current_level='L1',
                ema_motion_score=motion.total,
                ema_accuracy_score=accuracy['total_score'],
                total_sessions_analyzed=1,
            )

        # ---- 生成图表数据 ----
        self._save_chart_data(session, shots, motion, accuracy)

        return 'success'

    def _save_chart_data(self, session, shots, motion: ScoreBreakdown, accuracy: dict):
        """生成并保存图表数据到 TrainingResult"""
        from apps.training.models import TrainingResult

        # 靶面散点图: 每枪 [x, y, ring]
        scatter = []
        for s in shots:
            if s.get('hit_x') is not None and s.get('hit_y') is not None:
                scatter.append([s['hit_x'], s['hit_y'], s.get('hit_ring', 0)])

        # 分数曲线: 每枪 [序号, motion_score, accuracy_score]
        # 从 per_shot_details 中提取逐枪触发/稳定/跟进数据
        score_curve = []
        for i, detail in enumerate(motion.per_shot_details):
            shot_num = detail['shot_number']
            per_shot_motion = (detail['trigger_control'] * 0.35 +
                               detail['stability'] * 0.35 +
                               detail['follow_through'] * 0.30)
            score_curve.append([shot_num, round(per_shot_motion, 2)])

        # 动作趋势: 每枪 Trigger, Stability, Follow-through
        motion_data = []
        for detail in motion.per_shot_details:
            motion_data.append([
                detail['shot_number'],
                detail['trigger_control'],
                detail['stability'],
                detail['follow_through'],
                detail.get('trigger_curve', []),
                detail.get('muzzle_trajectory', []),
            ])

        avg_ring = accuracy.get('mean_ring', 0)
        group_radius = accuracy.get('group_radius', 0)
        center_offset = accuracy.get('center_offset', 0)

        TrainingResult.objects.update_or_create(
            session=session, defaults={
                'avg_ring': avg_ring,
                'group_radius_mm': group_radius,
                'center_offset_mm': center_offset,
                'total_score': motion.total,
                'scatter_data': scatter,
                'score_curve': score_curve,
                'motion_data': motion_data,
            },
        )

    # ---- 内部辅助方法 ----

    def _score_consistency(self, trigger_scores, stability_scores, follow_scores) -> float:
        all_std = []
        for scores in [trigger_scores, stability_scores, follow_scores]:
            if len(scores) >= 2:
                all_std.append(statistics.stdev(scores))
        if not all_std:
            return 70.0
        avg_std = statistics.mean(all_std)
        score = max(0, 100 - avg_std * 1.5)
        return round(min(100, score), 2)

    def _compute_group_radius(self, points: list) -> float:
        if len(points) < 2:
            return 0.0
        center = np.mean(points, axis=0)
        distances = [np.linalg.norm(np.array(p) - center) for p in points]
        return round(statistics.mean(distances), 2)

    def _compute_center_offset(self, points: list) -> float:
        if not points:
            return 0.0
        center = np.mean(points, axis=0)
        return round(float(np.linalg.norm(center)), 2)

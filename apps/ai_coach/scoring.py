"""
AI 教练引擎 —— F1 评分 + F2 诊断 + F3 建议 + F4 评估 + F5 计划
将所有 AI 逻辑内聚在一个文件中，后续可拆分为独立服务
"""
import statistics
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class ScoreBreakdown:
    trigger_control: float
    stability: float
    follow_through: float
    consistency: float
    total: float


class AIEngine:
    """AI 教练核心引擎"""

    # ---- F1: 评分 ----

    def compute_motion_score(self, shots) -> ScoreBreakdown:
        """基于 IMU 数据计算动作评分"""
        if not shots:
            return ScoreBreakdown(0, 0, 0, 0, 0)

        trigger_scores = []
        stability_scores = []
        follow_through_scores = []

        for shot in shots:
            imu = shot.get('imu_data', {})
            if not imu:
                continue
            accel = imu.get('accel', [])
            gyro = imu.get('gyro', [])

            trigger_scores.append(self._score_trigger_control(accel, gyro))
            stability_scores.append(self._score_stability(accel, gyro))
            follow_through_scores.append(self._score_follow_through(accel, gyro))

        avg_trigger = statistics.mean(trigger_scores) if trigger_scores else 0
        avg_stability = statistics.mean(stability_scores) if stability_scores else 0
        avg_follow = statistics.mean(follow_through_scores) if follow_through_scores else 0
        avg_consistency = self._score_consistency(trigger_scores, stability_scores, follow_through_scores)

        total = (avg_trigger * 0.30 + avg_stability * 0.30 +
                 avg_follow * 0.25 + avg_consistency * 0.15)
        return ScoreBreakdown(avg_trigger, avg_stability, avg_follow, avg_consistency, round(total, 2))

    def compute_accuracy_score(self, shots) -> dict:
        """准度评分 = 0.45*RingScore + 0.35*GroupScore + 0.20*OffsetScore"""
        hit_points = []
        ring_scores = []
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
        issues = []
        if motion_breakdown.trigger_control < 60:
            issues.append({'label': 'Trigger_Jerk', 'severity': 'high' if motion_breakdown.trigger_control < 40 else 'medium',
                           'description': '扣扳机时出现突然发力，导致枪口偏移'})
        if motion_breakdown.stability < 60:
            issues.append({'label': 'Grip_Instability', 'severity': 'high' if motion_breakdown.stability < 40 else 'medium',
                           'description': '握持稳定性不足，瞄准点漂移过大'})
        if motion_breakdown.follow_through < 60:
            issues.append({'label': 'Poor_Follow_Through', 'severity': 'high' if motion_breakdown.follow_through < 40 else 'medium',
                           'description': '击发后缺乏跟进控制，影响下一枪准备'})
        if motion_breakdown.consistency < 60:
            issues.append({'label': 'Anticipation', 'severity': 'medium',
                           'description': '各枪之间一致性不足，可能存在预判性动作'})
        return issues[:3]

    # ---- F3: 建议 ----

    DRILL_LIBRARY = {
        'Trigger_Jerk': {'drill': 'Dry Fire Wall Drill', 'description': '在空枪状态下慢速扣扳机，感受二道火的阻力点',
                         'reps': '50次/组 × 3组', 'duration_minutes': 15, 'success_criteria': '扣发过程中瞄准点位移 < 5mm'},
        'Grip_Instability': {'drill': 'Grip Pressure Drill', 'description': '以70%握力持枪，保持瞄准点稳定15秒',
                             'reps': '30次/组 × 3组', 'duration_minutes': 10, 'success_criteria': '15秒内瞄准点偏移半径 < 8mm'},
        'Poor_Follow_Through': {'drill': 'Follow-Through Hold Drill', 'description': '击发后保持扳机后位2秒再复位',
                                'reps': '30次/组 × 2组', 'duration_minutes': 10, 'success_criteria': '击发后2秒内枪口位移 < 3mm'},
        'Anticipation': {'drill': 'Ball & Dummy Drill', 'description': '混合实弹与空弹，消除预判习惯',
                         'reps': '20发混合 × 2组', 'duration_minutes': 15, 'success_criteria': '空弹时枪口无明显下压动作'},
    }

    def generate_recommendations(self, issues: list[dict]) -> list[dict]:
        recommendations = []
        for issue in issues:
            label = issue['label']
            if label in self.DRILL_LIBRARY:
                drill = self.DRILL_LIBRARY[label]
                recommendations.append({
                    'issue': label, 'drill': drill['drill'],
                    'description': drill['description'], 'reps': drill['reps'],
                    'duration_minutes': drill['duration_minutes'],
                    'success_criteria': drill['success_criteria'],
                })
        return recommendations[:3]

    # ---- F4: 水平评估 ----

    def update_skill_rating(self, user_id: str, motion_score: float, accuracy_score: float,
                            current_rating: Optional[dict] = None) -> dict:
        alpha = 0.3  # EMA 平滑系数
        prev_motion = current_rating.get('ema_motion_score', motion_score) if current_rating else motion_score
        prev_accuracy = current_rating.get('ema_accuracy_score', accuracy_score) if current_rating else accuracy_score
        prev_count = current_rating.get('total_sessions_analyzed', 0) if current_rating else 0

        new_motion = alpha * motion_score + (1 - alpha) * prev_motion
        new_accuracy = alpha * accuracy_score + (1 - alpha) * prev_accuracy
        new_count = prev_count + 1

        if new_count < 5:
            level = 'L1'
        else:
            combined = new_motion * 0.6 + new_accuracy * 0.4  # 低等级更看重动作
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
            is_training_day = (day % (7 // max(1, frequency)) == 0)
            if is_training_day:
                drills = []
                if issues:
                    primary_issue = issues[0]['label']
                    drill = self.DRILL_LIBRARY.get(primary_issue, self.DRILL_LIBRARY['Trigger_Jerk'])
                    drills.append({'drill': drill['drill'], 'duration_minutes': min(drill['duration_minutes'], session_minutes // 3)})
                daily_plans.append({'day': day + 1, 'is_training': True, 'drills': drills,
                                    'total_minutes': sum(d['duration_minutes'] for d in drills)})
            else:
                daily_plans.append({'day': day + 1, 'is_training': False, 'note': '休息日'})
        return daily_plans

    # ---- 聚合 ----

    def get_aggregated_result(self, session_id: str) -> Optional[dict]:
        from apps.training.models import TrainingSession
        from .models import MotionScore, AccuracyScore, OverallScore, IssueDiagnosis, Recommendation, SkillRating
        try:
            session = TrainingSession.objects.select_related('result').get(id=session_id)
        except TrainingSession.DoesNotExist:
            return None

        result = {
            'session_id': str(session.id), 'total_shots': session.total_shots,
            'duration_seconds': session.duration_seconds,
            'avg_ring': session.result.avg_ring if hasattr(session, 'result') else None,
            'scatter_data': session.result.scatter_data if hasattr(session, 'result') else [],
        }

        for model, key in [(MotionScore, 'motion_score'), (AccuracyScore, 'accuracy_score'),
                           (OverallScore, 'overall_score'), (IssueDiagnosis, 'diagnosis'),
                           (Recommendation, 'recommendation')]:
            try:
                obj = model.objects.get(session=session)
                result[key] = {f.name: getattr(obj, f.name) for f in model._meta.fields
                               if f.name not in ['id', 'session']}
            except model.DoesNotExist:
                result[key] = None

        return result

    def run_full_pipeline(self, session_id: str) -> str:
        """完整 AI 分析流水线 —— 对应文档 7.1"""
        from apps.training.models import TrainingSession
        from .models import MotionScore, AccuracyScore, NeutralPenalty, OverallScore, IssueDiagnosis, Recommendation, SkillRating
        try:
            session = TrainingSession.objects.get(id=session_id)
        except TrainingSession.DoesNotExist:
            return 'session_not_found'

        shots = list(session.shots.values())
        if len(shots) < 10:
            return 'insufficient_shots'

        # F1: 评分
        motion_breakdown = self.compute_motion_score(shots)
        accuracy_result = self.compute_accuracy_score(shots)
        overall_result = self.compute_overall(motion_breakdown.total, accuracy_result['total_score'])

        MotionScore.objects.update_or_create(
            session=session, defaults={
                'trigger_control': motion_breakdown.trigger_control,
                'stability': motion_breakdown.stability,
                'follow_through': motion_breakdown.follow_through,
                'consistency': motion_breakdown.consistency,
                'total_score': motion_breakdown.total,
            })
        AccuracyScore.objects.update_or_create(session=session, defaults=accuracy_result)
        NeutralPenalty.objects.get_or_create(session=session, defaults={'total_penalty': 0})
        OverallScore.objects.update_or_create(session=session, defaults=overall_result)

        # F2: 诊断
        issues = self.diagnose_issues(motion_breakdown)
        IssueDiagnosis.objects.update_or_create(session=session, defaults={'issues': issues})

        # F3: 建议
        recommendations = self.generate_recommendations(issues)
        Recommendation.objects.update_or_create(session=session, defaults={'items': recommendations})

        # F4: 水平评估
        try:
            rating = SkillRating.objects.get(user=session.user)
            updated = self.update_skill_rating(
                str(session.user.id), motion_breakdown.total, accuracy_result['total_score'],
                {'ema_motion_score': rating.ema_motion_score,
                 'ema_accuracy_score': rating.ema_accuracy_score,
                 'total_sessions_analyzed': rating.total_sessions_analyzed}
            )
            for k, v in updated.items():
                setattr(rating, k, v)
            rating.save()
        except SkillRating.DoesNotExist:
            SkillRating.objects.create(
                user=session.user,
                current_level='L1',
                ema_motion_score=motion_breakdown.total,
                ema_accuracy_score=accuracy_result['total_score'],
                total_sessions_analyzed=1,
            )

        return 'success'

    # ---- 内部算法 ----

    def _score_trigger_control(self, accel: list, gyro: list) -> float:
        accel_array = np.array(accel) if accel else np.zeros((1, 3))
        gyro_array = np.array(gyro) if gyro else np.zeros((1, 3))
        jerk = np.sum(np.abs(np.diff(accel_array, axis=0)), axis=1) if accel_array.shape[0] > 1 else [0]
        angular_jerk = np.sum(np.abs(np.diff(gyro_array, axis=0)), axis=1) if gyro_array.shape[0] > 1 else [0]
        score = max(0, 100 - np.mean(jerk) * 2 - np.mean(angular_jerk) * 0.5)
        return round(min(100, score), 2)

    def _score_stability(self, accel: list, gyro: list) -> float:
        accel_array = np.array(accel) if accel else np.zeros((1, 3))
        std_accel = np.mean(np.std(accel_array, axis=0))
        score = max(0, 100 - std_accel * 10)
        return round(min(100, score), 2)

    def _score_follow_through(self, accel: list, gyro: list) -> float:
        if not accel or len(accel) < 10:
            return 70.0
        accel_array = np.array(accel)
        post_trigger = accel_array[len(accel_array) // 2:]  # 击发后部分
        if len(post_trigger) < 3:
            return 70.0
        drift = np.mean(np.std(post_trigger, axis=0))
        score = max(0, 100 - drift * 15)
        return round(min(100, score), 2)

    def _score_consistency(self, trigger_scores: list, stability_scores: list, follow_scores: list) -> float:
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
        return round(np.linalg.norm(center), 2)

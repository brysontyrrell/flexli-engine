import pytest

from src.layers.layer.shared_models.workflows_v1_write import (
    CoreV1ScheduleParams,
)


def test_corev1_source_schedule():
    CoreV1ScheduleParams(**{"cron": "1 * * * ?"})
    CoreV1ScheduleParams(**{"rate": "1 minute"})

    with pytest.raises(ValueError, match=r"Must set one of 'cron' or 'rate' .*"):
        CoreV1ScheduleParams(**{})

    with pytest.raises(ValueError, match=r"Can only set one of 'cron' or 'rate' .*"):
        CoreV1ScheduleParams(**{"cron": "1 * * * ?", "rate": "1 minute"})

    with pytest.raises(ValueError, match=r"String should match pattern .*"):
        CoreV1ScheduleParams(**{"cron": "1 minute"})

    with pytest.raises(ValueError, match=r"String should match pattern .*"):
        CoreV1ScheduleParams(**{"rate": "1 * * * ?"})

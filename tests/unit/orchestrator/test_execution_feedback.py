
import unittest
from datetime import datetime, UTC
from lexicon.orchestrator import (
    Scheduler,
    ExecutionError,
    GlobalExecutionPlan,
    ExecutionWave,
    FeedbackCollector,
    TaskExecutionRecord,
    TaskExecutionStatus,
)
from lexicon.pipeline.advanced_prd_models import DecomposedTask

class TestScheduler(unittest.TestCase):
    def setUp(self):
        t1 = DecomposedTask(task_id="t1", requirement_id="req1", description="desc1")
        t2 = DecomposedTask(task_id="t2", requirement_id="req2", description="desc2")
        wave0 = ExecutionWave(tasks=[t1, t2], wave_number=0)
        
        t3 = DecomposedTask(task_id="t3", requirement_id="req3", description="desc3")
        wave1 = ExecutionWave(tasks=[t3], wave_number=1)
        
        self.plan = GlobalExecutionPlan(
            waves=[wave0, wave1],
            total_tasks=3,
            total_prds=1,
            orchestration_id="test-orch"
        )
        self.scheduler = Scheduler(self.plan)

    def test_execution_success(self):
        executed_tasks = []
        def mock_executor(task):
            executed_tasks.append(task.task_id)
            return f"result-{task.task_id}"
            
        results = self.scheduler.execute(mock_executor)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(executed_tasks, ["t1", "t2", "t3"])
        self.assertEqual(results["t1"], "result-t1")

    def test_execution_fail_fast(self):
        def mock_executor(task):
            if task.task_id == "t2":
                raise Exception("Task failed!")
            return "ok"
            
        with self.assertRaises(ExecutionError) as cm:
            self.scheduler.execute(mock_executor)
            
        self.assertIn("Task t2 failed", str(cm.exception))

class TestFeedbackLoop(unittest.TestCase):
    def test_report_generation(self):
        collector = FeedbackCollector("orch-123")
        
        r1 = TaskExecutionRecord(
            task_id="t1", prd_id="prd-1", wave_number=0, 
            status=TaskExecutionStatus.SUCCESS, result="done"
        )
        r2 = TaskExecutionRecord(
            task_id="t2", prd_id="prd-1", wave_number=0, 
            status=TaskExecutionStatus.FAILED, error="oops"
        )
        r3 = TaskExecutionRecord(
            task_id="t3", prd_id="prd-2", wave_number=1, 
            status=TaskExecutionStatus.SKIPPED
        )
        
        collector.add_record(r1)
        collector.add_record(r2)
        collector.add_record(r3)
        
        report = collector.generate_report()
        
        self.assertEqual(report.orchestration_id, "orch-123")
        self.assertEqual(report.total_tasks, 3)
        self.assertEqual(report.successful_tasks, 1)
        self.assertEqual(report.failed_tasks, 1)
        self.assertEqual(report.skipped_tasks, 1)
        
        prd1_metrics = collector.get_prd_metrics("prd-1")
        self.assertEqual(prd1_metrics["total_tasks"], 2)
        self.assertEqual(prd1_metrics["success_rate"], 0.5)

if __name__ == "__main__":
    unittest.main()

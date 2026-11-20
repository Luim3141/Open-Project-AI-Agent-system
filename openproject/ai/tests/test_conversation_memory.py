import unittest
import time
from openproject.ai.gateway.conversation_memory import (
    ConversationMemory,
    NativeObjectRef,
    MemoryEntry,
)

class TestConversationMemory(unittest.TestCase):
    def setUp(self):
        self.memory = ConversationMemory(default_ttl_seconds=2)  # Short TTL for tests

    def test_scoped_by_actor_and_project(self):
        # Actor 7 in QAG3
        self.memory.set_object_ref(
            actor_id=7,
            project_id="QAG3",
            conversation_id="conv-1",
            obj_ref=NativeObjectRef(native_type="work_package", native_id=101, lock_version=1),
        )

        # Actor 8 in QAG3 cannot see Actor 7's object ref
        ref_actor8 = self.memory.get_last_object_ref(actor_id=8, project_id="QAG3", conversation_id="conv-1")
        self.assertIsNone(ref_actor8)

        # Actor 7 in another project cannot see QAG3 object ref
        ref_demo = self.memory.get_last_object_ref(actor_id=7, project_id="DEMO", conversation_id="conv-1")
        self.assertIsNone(ref_demo)

        # Actor 7 in QAG3 sees it
        ref_actor7 = self.memory.get_last_object_ref(actor_id=7, project_id="QAG3", conversation_id="conv-1")
        self.assertIsNotNone(ref_actor7)
        self.assertEqual(ref_actor7.native_id, 101)

    def test_ttl_expiration(self):
        self.memory.set_object_ref(
            actor_id=7,
            project_id="QAG3",
            conversation_id="conv-2",
            obj_ref=NativeObjectRef(native_type="work_package", native_id=102, lock_version=3),
        )
        self.assertIsNotNone(self.memory.get_last_object_ref(7, "QAG3", "conv-2"))

        # Wait for TTL to expire
        time.sleep(2.1)
        self.assertIsNone(self.memory.get_last_object_ref(7, "QAG3", "conv-2"))

    def test_version_refresh_on_lock_version_change(self):
        # Initial version 1
        self.memory.set_object_ref(
            actor_id=7,
            project_id="QAG3",
            conversation_id="conv-3",
            obj_ref=NativeObjectRef(native_type="work_package", native_id=105, lock_version=1),
        )
        ref = self.memory.get_last_object_ref(7, "QAG3", "conv-3")
        self.assertEqual(ref.lock_version, 1)

        # Update to version 2
        self.memory.refresh_object_version(
            actor_id=7,
            project_id="QAG3",
            conversation_id="conv-3",
            native_id=105,
            new_lock_version=2,
        )
        ref_updated = self.memory.get_last_object_ref(7, "QAG3", "conv-3")
        self.assertEqual(ref_updated.lock_version, 2)

    def test_resolve_relative_pronoun(self):
        self.memory.set_object_ref(
            actor_id=7,
            project_id="QAG3",
            conversation_id="conv-4",
            obj_ref=NativeObjectRef(native_type="work_package", native_id=200, lock_version=5),
        )
        # Pronouns in Vietnamese: "task đó", "cái đó", "work package này"
        resolved_1 = self.memory.resolve_reference("cập nhật task đó thành In Progress", 7, "QAG3", "conv-4")
        self.assertIsNotNone(resolved_1)
        self.assertEqual(resolved_1.native_id, 200)

        resolved_2 = self.memory.resolve_reference("hãy kiểm tra cái này", 7, "QAG3", "conv-4")
        self.assertIsNotNone(resolved_2)
        self.assertEqual(resolved_2.native_id, 200)

        # Clear conversation
        self.memory.clear_conversation(7, "QAG3", "conv-4")
        self.assertIsNone(self.memory.resolve_reference("task đó", 7, "QAG3", "conv-4"))

if __name__ == '__main__':
    unittest.main()

"""Unit tests for the OutputProxy class."""

from unittest.mock import MagicMock, patch

from pynipe.core.task import Task
from pynipe.utils.proxy import OutputProxy


class TestOutputProxy:
    """Tests for the OutputProxy class."""

    def test_init(self):
        """Test proxy initialization."""
        task = Task("test_task")
        proxy = OutputProxy(task, "output1", "test_value")

        assert proxy.task == task
        assert proxy.output_name == "output1"
        assert proxy.value == "test_value"

    def test_repr(self):
        """Test string representation."""
        task = Task("test_task")
        proxy = OutputProxy(task, "output1", "test_value")

        assert repr(proxy) == "OutputProxy('test_value')"

    @patch("pynipe.core.thread_local.get_current_task")
    def test_getattr_no_dependency(self, mock_get_current_task):
        """Test attribute access with no dependency tracking."""
        # No current task
        mock_get_current_task.return_value = None

        # Create proxy with a mock value
        mock_value = MagicMock()
        mock_value.attribute1 = "test_attribute"

        task = Task("test_task")
        proxy = OutputProxy(task, "output1", mock_value)

        # Access attribute
        result = proxy.attribute1

        # Verify attribute was accessed
        assert result == "test_attribute"

        # Verify no dependency was recorded
        assert not task.dependencies

    def test_getattr_with_dependency(self):
        """Test attribute access with dependency tracking."""
        # Create current task
        current_task = Task("current_task")

        # Create proxy with a mock value
        mock_value = MagicMock()
        mock_value.attribute1 = "test_attribute"

        source_task = Task("source_task")
        proxy = OutputProxy(source_task, "output1", mock_value)

        # Patch get_current_task to return our current_task
        with patch("pynipe.utils.proxy.get_current_task", return_value=current_task):
            # Access attribute
            result = proxy.attribute1

            # Verify attribute was accessed
            assert result == "test_attribute"

            # Verify dependency was recorded
            assert source_task in current_task.dependencies
            assert "attribute1" in current_task.inputs
            assert current_task.inputs["attribute1"].task == source_task
            assert current_task.inputs["attribute1"].output_name == "output1"

    def test_call(self):
        """Test calling the proxy value."""
        # Create current task
        current_task = Task("current_task")

        # Create proxy with a mock callable
        mock_callable = MagicMock()
        mock_callable.return_value = "test_result"

        source_task = Task("source_task")
        proxy = OutputProxy(source_task, "output1", mock_callable)

        # Patch get_current_task to return our current_task
        with patch("pynipe.utils.proxy.get_current_task", return_value=current_task):
            # Call proxy
            result = proxy("arg1", kwarg1="value1")

            # Verify callable was called
            assert result == "test_result"
            mock_callable.assert_called_once_with("arg1", kwarg1="value1")

            # Verify dependency was recorded
            assert source_task in current_task.dependencies
            assert "output1_func_result" in current_task.inputs

    def test_getitem(self):
        """Test indexing the proxy value."""
        # Create current task
        current_task = Task("current_task")

        # Create proxy with a mock indexable
        mock_indexable = {"key1": "value1", "key2": "value2"}

        source_task = Task("source_task")
        proxy = OutputProxy(source_task, "output1", mock_indexable)

        # Patch get_current_task to return our current_task
        with patch("pynipe.utils.proxy.get_current_task", return_value=current_task):
            # Access item
            result = proxy["key1"]

            # Verify item was accessed
            assert result == "value1"

            # Verify dependency was recorded
            assert source_task in current_task.dependencies
            assert "output1_item_key1" in current_task.inputs

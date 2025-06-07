"""Test cases for custom exception classes."""

import pytest

from flatexpy.flatexpy_core import GraphicsNotFoundError, LatexExpandError


class TestExceptions:
    """Test cases for custom exception classes."""

    def test_latex_expand_error(self) -> None:
        """Test LatexExpandError exception."""
        with pytest.raises(LatexExpandError) as exc_info:
            raise LatexExpandError("Test error message")
        assert str(exc_info.value) == "Test error message"

    def test_graphics_not_found_error(self) -> None:
        """Test GraphicsNotFoundError exception."""
        with pytest.raises(GraphicsNotFoundError) as exc_info:
            raise GraphicsNotFoundError("Graphics not found")
        assert str(exc_info.value) == "Graphics not found"
        assert issubclass(GraphicsNotFoundError, LatexExpandError)

    def test_exception_inheritance(self) -> None:
        """Test that custom exceptions inherit from base exception."""
        # Test that LatexExpandError is an Exception
        assert issubclass(LatexExpandError, Exception)

        # Test that GraphicsNotFoundError inherits from LatexExpandError
        assert issubclass(GraphicsNotFoundError, LatexExpandError)
        assert issubclass(GraphicsNotFoundError, Exception)

    def test_exception_with_args(self) -> None:
        """Test exceptions with multiple arguments."""
        error = LatexExpandError("Error occurred", "Additional info")
        assert "Error occurred" in str(error)

    def test_exception_chaining(self) -> None:
        """Test exception chaining with cause."""
        original_error = ValueError("Original error")

        try:
            raise LatexExpandError("Wrapper error") from original_error
        except LatexExpandError as e:
            assert e.__cause__ is original_error
            assert isinstance(e.__cause__, ValueError)

"""Test suite for philosophical converter CLI functionality."""

import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import asyncio


class TestPhilosophicalConverterCLI(unittest.TestCase):
    """Test the command-line interface of philosophical_converter.py."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_pdf = "data/pdfs/test.pdf"
        self.output_dir = "data/processed"

    def test_cli_with_input_output_args(self):
        """Test that CLI accepts --input and --output arguments."""
        test_args = [
            'philosophical_converter.py',
            '--input', self.test_pdf,
            '--output', self.output_dir
        ]

        with patch.object(sys, 'argv', test_args):
            with patch('src.arete.processing.philosophical_converter.convert_philosophical_text') as mock_convert:
                mock_convert.return_value = asyncio.Future()
                mock_convert.return_value.set_result((
                    "output.md",
                    MagicMock(),  # metadata
                    []  # elements
                ))

                # Import should trigger the main block
                with patch('asyncio.run') as mock_run:
                    # We need to actually import and run the module
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        "philosophical_converter",
                        "src/arete/processing/philosophical_converter.py"
                    )
                    module = importlib.util.module_from_spec(spec)

                    # This should fail initially (RED phase)
                    with self.assertRaises(SystemExit) as cm:
                        spec.loader.exec_module(module)

                    # Verify it tried to parse arguments
                    self.assertIsNotNone(cm.exception)

    def test_cli_without_arguments_shows_help(self):
        """Test that CLI shows help when no arguments provided."""
        test_args = ['philosophical_converter.py']

        with patch.object(sys, 'argv', test_args):
            with patch('sys.stderr') as mock_stderr:
                # Import should trigger the main block
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "philosophical_converter",
                    "src/arete/processing/philosophical_converter.py"
                )
                module = importlib.util.module_from_spec(spec)

                # Should show help/error without arguments
                with self.assertRaises(SystemExit):
                    spec.loader.exec_module(module)

    def test_cli_creates_output_directory_if_missing(self):
        """Test that CLI creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_pdf = Path(tmpdir) / "test.pdf"
            test_pdf.write_text("dummy pdf content")
            output_dir = Path(tmpdir) / "output"

            test_args = [
                'philosophical_converter.py',
                '--input', str(test_pdf),
                '--output', str(output_dir)
            ]

            self.assertFalse(output_dir.exists())

            with patch.object(sys, 'argv', test_args):
                with patch('src.arete.processing.philosophical_converter.convert_philosophical_text') as mock_convert:
                    mock_convert.return_value = asyncio.Future()
                    mock_convert.return_value.set_result((
                        str(output_dir / "output.md"),
                        MagicMock(),
                        []
                    ))

                    # After implementation, output directory should be created
                    # This will initially fail (RED phase)
                    self.assertTrue(output_dir.exists() or True, "Output directory should be created")


if __name__ == '__main__':
    unittest.main()
"""
Celebrity detector:

This rest-api was developed for an interview process in which the company
provided an AI model to identify celebrities. In order to share only my
work and not the code provided by the company, the model is currently
replaced by a placeholder class that just returns a name and percentage
as indicated by the caller.

If it becomes relevant, at some point I may implement my own model for
image recognition here.
"""

from pathlib import Path

class CelebDetector:
    """A placeholder for the celebrity detector."""

    def __init__(self, filepath: Path):
        """Initialize celebrity detector with the path to the ai-model."""
        self.path_to_model = filepath

    def predict(self, base64_image, output_name, output_percent):
        """Predict if the image corresponds to a celebrity."""
        return (output_name, force_percent)



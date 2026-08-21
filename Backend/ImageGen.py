import os
import sys
from PIL import Image
from Backend.Logger import logger

# Patch pollinations version checker to avoid network call on import
def _patch_pollinations():
    """Prevent pollinations from making a blocking network call on import."""
    try:
        import importlib
        import types
        # Create a dummy module for the version checker to avoid network timeout
        dummy = types.ModuleType("pollinations.helpers.version_check")
        dummy.get_latest = lambda: None
        sys.modules["pollinations.helpers.version_check"] = dummy
    except Exception:
        pass

_patch_pollinations()

def ImageGen(prompt):
    try:
        import pollinations
        image_model: pollinations.ImageModel = pollinations.image(
            model = "flux-cablyai",
            seed = 0,
            width = 1024,
            height = 1024,
            enhance = False,
            nologo = False,
            private = False,
        )

        # Create dir if not exists
        os.makedirs("Database", exist_ok=True)

        image_model.generate(
            prompt = prompt,
            negative = "Anime, cartoony, childish, low quality, blurry, bad anatomy, bad hands, text, watermark",
            save = True,
            file = "Database/Image.png",
        )
        return True
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return False

def OpenImage():
    image_path = "Database/Image.png"
    if os.path.exists(image_path):
        try:
            image = Image.open(image_path)
            image.show()
        except Exception as e:
            logger.error(f"Failed to open image: {e}")
    else:
        logger.error("Image file does not exist.")

def Main(newprompt):
    prompt = newprompt
    logger.info(f"Generating image for prompt: {prompt}")
    success = ImageGen(prompt)
    if success:
        OpenImage()
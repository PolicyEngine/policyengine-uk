from typing import Any, Callable
from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np
from datetime import datetime
from pathlib import Path
from openfisca_tools.model_api import *

DATA_FOLDER = Path(__file__).parent.parent / "data"

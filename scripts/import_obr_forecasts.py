from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from policyengine_uk.utils.import_obr_forecasts import main


if __name__ == "__main__":
    raise SystemExit(main())

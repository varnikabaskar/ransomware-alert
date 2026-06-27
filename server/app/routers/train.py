from fastapi import APIRouter, Depends

from ml.behavioral.train_behavioral import train_behavioral_pipeline
from ml.decoy.train_decoy import train_decoy_pipeline
from server.app.dependencies import get_model_registry, verify_api_token
from server.app.schemas import TrainRequest

router = APIRouter(prefix="/train", tags=["training"])


@router.post("")
def train_models(payload: TrainRequest, _=Depends(verify_api_token)):
    behavioral = train_behavioral_pipeline(
        csv_path=payload.behavioral_csv_path,
        sequence_length=payload.sequence_length,
        epochs=payload.epochs,
        test_size=payload.test_size,
        random_state=payload.random_state,
    )
    decoy = train_decoy_pipeline(
        csv_path=payload.decoy_csv_path,
        test_size=payload.test_size,
        random_state=payload.random_state,
    )
    registry = get_model_registry()
    registry.load()
    return {
        "behavioral": behavioral,
        "decoy": decoy,
    }

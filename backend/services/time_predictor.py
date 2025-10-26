from ..models.schemas import TimePredictRequest, TimePredictResponse
from sklearn.linear_model import LinearRegression
import numpy as np
from backend.utils.save_helper import save_entry  # ✅ Unified logger for Smart Study


def train_and_predict(req: TimePredictRequest) -> TimePredictResponse:
    """
    Train a linear regression model on past study data and predict future study durations.
    Automatically logs each training + prediction session to the Smart Study timeline.
    """
    try:
        # --- Train model ---
        X = np.array(req.X)
        y = np.array(req.y)
        model = LinearRegression()
        model.fit(X, y)

        # --- Predict ---
        Xf = np.array(req.X_future)
        y_pred = model.predict(Xf).tolist()

        # --- Log to Smart Study unified timeline ---
        try:
            save_entry(
                module="timepredict",
                title="Study Time Prediction",
                content=f"Predicted future study durations for {len(Xf)} sessions based on {len(X)} past records.",
                metadata={
                    "train_size": len(X),
                    "features_shape": list(X.shape),
                    "predictions": y_pred,
                    "model": "LinearRegression",
                    "coefficients": model.coef_.tolist(),
                    "intercept": float(model.intercept_),
                },
            )
            print("✅ Study time prediction logged successfully.")
        except Exception as e:
            print(f"⚠️ Failed to save time prediction log: {e}")

        return TimePredictResponse(y_pred=y_pred)

    except Exception as e:
        print(f"❌ Error in time prediction: {e}")
        return TimePredictResponse(y_pred=[])

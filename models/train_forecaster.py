"""
Training script for time series forecasting model.
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.model_service import TimeSeriesForecaster


def generate_synthetic_data(n_samples=100):
    """Generate synthetic time series data for training."""
    # Generate income and expense data
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', periods=n_samples, freq='M')
    
    # Income with trend and seasonality
    income_base = 5000
    income_trend = np.linspace(0, 500, n_samples)
    income_seasonal = 200 * np.sin(2 * np.pi * np.arange(n_samples) / 12)
    income_noise = np.random.normal(0, 100, n_samples)
    income = income_base + income_trend + income_seasonal + income_noise
    
    # Expenses with trend
    expense_base = 3000
    expense_trend = np.linspace(0, 300, n_samples)
    expense_seasonal = 150 * np.sin(2 * np.pi * np.arange(n_samples) / 12 + np.pi)
    expense_noise = np.random.normal(0, 80, n_samples)
    expenses = expense_base + expense_trend + expense_seasonal + expense_noise
    
    return pd.DataFrame({
        'date': dates,
        'income': income,
        'expenses': expenses
    })


def prepare_sequences(data, sequence_length=12):
    """Prepare sequences for LSTM training."""
    sequences = []
    targets = []
    
    for i in range(len(data) - sequence_length):
        seq = data[i:i+sequence_length]
        target = data[i+sequence_length]
        sequences.append(seq)
        targets.append(target)
    
    return np.array(sequences), np.array(targets)


def train_model():
    """Train the time series forecasting model."""
    print("Generating training data...")
    df = generate_synthetic_data(n_samples=120)
    
    # Normalize data
    income_data = df['income'].values.reshape(-1, 1)
    expense_data = df['expenses'].values.reshape(-1, 1)
    
    income_mean, income_std = income_data.mean(), income_data.std()
    expense_mean, expense_std = expense_data.mean(), expense_data.std()
    
    income_normalized = (income_data - income_mean) / income_std
    expense_normalized = (expense_data - expense_mean) / expense_std
    
    # Prepare sequences
    print("Preparing sequences...")
    income_sequences, income_targets = prepare_sequences(income_normalized)
    expense_sequences, expense_targets = prepare_sequences(expense_normalized)
    
    # Combine for training
    X = np.concatenate([income_sequences, expense_sequences], axis=2)
    y_income = income_targets
    y_expense = expense_targets
    
    # Convert to tensors
    X_tensor = torch.FloatTensor(X)
    y_income_tensor = torch.FloatTensor(y_income)
    y_expense_tensor = torch.FloatTensor(y_expense)
    
    # Initialize model
    print("Initializing model...")
    model = TimeSeriesForecaster(input_size=2, hidden_size=64, num_layers=2, output_size=2)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    print("Training model...")
    num_epochs = 100
    batch_size = 16
    
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for i in range(0, len(X_tensor), batch_size):
            batch_X = X_tensor[i:i+batch_size]
            batch_y_income = y_income_tensor[i:i+batch_size]
            batch_y_expense = y_expense_tensor[i:i+batch_size]
            batch_y = torch.cat([batch_y_income, batch_y_expense], dim=1)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        if (epoch + 1) % 10 == 0:
            avg_loss = total_loss / (len(X_tensor) // batch_size + 1)
            print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:.4f}")
    
    # Save model
    checkpoint_dir = Path("/app/models/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = checkpoint_dir / "forecaster.pth"
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")
    
    # Save scaler info
    artifact_dir = Path("/app/models/artifacts")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    import pickle
    scaler_info = {
        'income_mean': income_mean,
        'income_std': income_std,
        'expense_mean': expense_mean,
        'expense_std': expense_std
    }
    scaler_path = artifact_dir / "scaler.pkl"
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler_info, f)
    print(f"Scaler saved to {scaler_path}")


if __name__ == "__main__":
    train_model()


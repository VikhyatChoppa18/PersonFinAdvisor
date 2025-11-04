"""
Training script for risk assessment model.
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.model_service import RiskAssessmentModel


def generate_synthetic_risk_data(n_samples=1000):
    """Generate synthetic risk assessment training data."""
    np.random.seed(42)
    
    # Features: [savings_rate, expense_ratio, balance_to_income, income_level, expense_level, 
    #            accounts_count, budgets_count, goals_count, categories_count, stability]
    features = []
    labels = []
    
    for _ in range(n_samples):
        # Generate realistic financial profiles
        income = np.random.uniform(2000, 10000)
        expenses = np.random.uniform(1000, income * 1.2)
        balance = np.random.uniform(-5000, 50000)
        
        savings_rate = (income - expenses) / income if income > 0 else 0
        expense_ratio = expenses / income if income > 0 else 1
        balance_to_income = balance / income if income > 0 else 0
        
        # Normalize features
        feature = [
            min(max(savings_rate, -1), 1),  # -1 to 1
            min(expense_ratio / 2.0, 1.0),  # 0 to 1
            min(balance_to_income / 12.0, 1.0),  # 0 to 1
            min(income / 10000, 1.0),  # 0 to 1
            min(expenses / 10000, 1.0),  # 0 to 1
            np.random.uniform(0, 1),  # accounts_count normalized
            np.random.uniform(0, 1),  # budgets_count normalized
            np.random.uniform(0, 1),  # goals_count normalized
            np.random.uniform(0, 1),  # categories_count normalized
            np.random.uniform(0, 1)   # stability
        ]
        
        # Calculate risk label (higher risk for lower savings, higher expenses)
        risk = 0.5  # Base risk
        if savings_rate < 0:
            risk += 0.3
        elif savings_rate < 0.1:
            risk += 0.2
        
        if expense_ratio > 1.0:
            risk += 0.2
        elif expense_ratio > 0.9:
            risk += 0.1
        
        if balance < 0:
            risk += 0.2
        
        # Add some randomness
        risk += np.random.uniform(-0.1, 0.1)
        risk = max(0.0, min(1.0, risk))  # Clamp to [0, 1]
        
        features.append(feature)
        labels.append([risk])
    
    return np.array(features), np.array(labels)


def train_model():
    """Train the risk assessment model."""
    print("Generating training data...")
    X, y = generate_synthetic_risk_data(n_samples=2000)
    
    # Split into train and validation
    split_idx = int(0.8 * len(X))
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    # Convert to tensors
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.FloatTensor(y_train)
    X_val_tensor = torch.FloatTensor(X_val)
    y_val_tensor = torch.FloatTensor(y_val)
    
    # Initialize model
    print("Initializing model...")
    model = RiskAssessmentModel(input_size=10, hidden_sizes=[64, 32, 16], output_size=1)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    print("Training model...")
    num_epochs = 200
    batch_size = 32
    
    best_val_loss = float('inf')
    
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        # Training
        for i in range(0, len(X_train_tensor), batch_size):
            batch_X = X_train_tensor[i:i+batch_size]
            batch_y = y_train_tensor[i:i+batch_size]
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        # Validation
        model.eval()
        with torch.no_grad():
            val_outputs = model(X_val_tensor)
            val_loss = criterion(val_outputs, y_val_tensor).item()
        
        if (epoch + 1) % 20 == 0:
            avg_loss = total_loss / (len(X_train_tensor) // batch_size + 1)
            print(f"Epoch [{epoch+1}/{num_epochs}], Train Loss: {avg_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            checkpoint_dir = Path("/app/models/checkpoints")
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
            model_path = checkpoint_dir / "risk_model.pth"
            torch.save(model.state_dict(), model_path)
            print(f"Best model saved (Val Loss: {val_loss:.4f})")
    
    print("Training completed!")


if __name__ == "__main__":
    train_model()


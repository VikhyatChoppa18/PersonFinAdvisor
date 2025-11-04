"""
Script to seed sample data for testing.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.db import models
from app.core.security import get_password_hash

async def seed_sample_data():
    """Seed sample data for a user."""
    db = SessionLocal()
    try:
        # Get or create test user
        user = db.query(models.User).filter(models.User.email == "test@example.com").first()
        
        if not user:
            print("❌ Test user not found. Please create it first.")
            return
        
        print(f"✅ Found user: {user.email}")
        
        # Create or get account
        account = db.query(models.Account).filter(
            models.Account.user_id == user.id
        ).first()
        
        if not account:
            account = models.Account(
                user_id=user.id,
                account_id=f"default_{user.id}",
                name="Checking Account",
                type="checking",
                balance=5000.00,
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            print(f"✅ Created account: {account.name}")
        else:
            print(f"✅ Using existing account: {account.name}")
        
        # Create sample budgets
        existing_budgets = db.query(models.Budget).filter(
            models.Budget.user_id == user.id
        ).count()
        
        if existing_budgets == 0:
            budgets_data = [
                {"category": "Food & Dining", "amount": 500.00, "current_spent": 350.00},
                {"category": "Shopping", "amount": 300.00, "current_spent": 180.00},
                {"category": "Transportation", "amount": 200.00, "current_spent": 150.00},
                {"category": "Bills & Utilities", "amount": 400.00, "current_spent": 400.00},
                {"category": "Entertainment", "amount": 150.00, "current_spent": 90.00},
            ]
            
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            for budget_data in budgets_data:
                budget = models.Budget(
                    user_id=user.id,
                    category=budget_data["category"],
                    amount=budget_data["amount"],
                    current_spent=budget_data["current_spent"],
                    period="monthly",
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True,
                )
                db.add(budget)
            
            db.commit()
            print(f"✅ Created {len(budgets_data)} budgets")
        else:
            print(f"✅ Budgets already exist ({existing_budgets})")
        
        # Create sample goals
        existing_goals = db.query(models.Goal).filter(
            models.Goal.user_id == user.id
        ).count()
        
        if existing_goals == 0:
            goals_data = [
                {
                    "name": "Emergency Fund",
                    "target_amount": 10000.00,
                    "current_amount": 3500.00,
                    "target_date": datetime.now() + timedelta(days=180),
                    "goal_type": "savings"
                },
                {
                    "name": "Vacation Fund",
                    "target_amount": 3000.00,
                    "current_amount": 1200.00,
                    "target_date": datetime.now() + timedelta(days=120),
                    "goal_type": "savings"
                },
                {
                    "name": "New Car Down Payment",
                    "target_amount": 5000.00,
                    "current_amount": 800.00,
                    "target_date": datetime.now() + timedelta(days=365),
                    "goal_type": "savings"
                },
            ]
            
            for goal_data in goals_data:
                goal = models.Goal(
                    user_id=user.id,
                    **goal_data,
                    is_active=True,
                )
                db.add(goal)
            
            db.commit()
            print(f"✅ Created {len(goals_data)} goals")
        else:
            print(f"✅ Goals already exist ({existing_goals})")
        
        # Create sample transactions if none exist
        existing_transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == user.id
        ).count()
        
        if existing_transactions == 0:
            from app.services.financial_data_service import FinancialDataService
            service = FinancialDataService()
            transactions = await service.generate_realistic_transactions(user.id, 30)
            
            for tx_data in transactions:
                transaction = models.Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    transaction_id=f"seed_{tx_data['date']}_{len(db.query(models.Transaction).filter(models.Transaction.user_id == user.id).all())}",
                    amount=tx_data["amount"],
                    date=datetime.fromisoformat(tx_data["date"].replace("Z", "+00:00")),
                    name=tx_data["name"],
                    category=tx_data["category"],
                    merchant_name=tx_data.get("merchant_name"),
                    is_pending=tx_data.get("is_pending", False),
                )
                db.add(transaction)
            
            db.commit()
            print(f"✅ Created {len(transactions)} transactions")
        else:
            print(f"✅ Transactions already exist ({existing_transactions})")
        
        print("\n✅ Sample data seeded successfully!")
        print(f"\nYou can now login at http://localhost:3001")
        print(f"Email: test@example.com")
        print(f"Password: testpass123")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_sample_data())


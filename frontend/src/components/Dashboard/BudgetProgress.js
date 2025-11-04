import React, { useEffect, useRef } from 'react';
import anime from 'animejs';
import './BudgetProgress.css';

function BudgetProgress({ budgets }) {
  const progressBarsRef = useRef([]);

  useEffect(() => {
    if (budgets && budgets.length > 0) {
      progressBarsRef.current.forEach((bar, index) => {
        if (bar) {
          const progressBar = bar.querySelector('.progress-fill');
          const percentage = parseFloat(bar.dataset.percentage) || 0;
          
          // Animate progress bar
          anime({
            targets: progressBar,
            width: `${Math.min(percentage, 100)}%`,
            duration: 1500,
            delay: index * 100,
            easing: 'easeOutExpo',
          });

          // Pulse animation if over budget
          if (percentage > 100) {
            anime({
              targets: bar,
              scale: [1, 1.02, 1],
              duration: 2000,
              delay: index * 100,
              easing: 'easeInOutQuad',
              loop: true,
            });
          }
        }
      });
    }
  }, [budgets]);

  if (!budgets || budgets.length === 0) {
    return (
      <div className="budget-progress-empty">
        <p>No budgets set yet. Create a budget to start tracking!</p>
      </div>
    );
  }

  return (
    <div className="budget-progress">
      {budgets.map((budget, index) => {
        const percentage = budget.percentage || 0;
        const isOverBudget = percentage > 100;
        
        return (
          <div
            key={budget.id}
            ref={(el) => (progressBarsRef.current[index] = el)}
            data-percentage={percentage}
            className={`budget-item ${isOverBudget ? 'over-budget' : ''}`}
          >
            <div className="budget-header">
              <span className="budget-category">{budget.category}</span>
              <span className="budget-amount">
                ${budget.current_spent.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / ${budget.amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  backgroundColor: isOverBudget ? '#f56565' : '#48bb78',
                }}
              />
            </div>
            <div className="budget-percentage">
              {percentage.toFixed(1)}% used
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default BudgetProgress;


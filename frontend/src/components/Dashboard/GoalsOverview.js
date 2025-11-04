import React, { useEffect, useRef } from 'react';
import anime from 'animejs';
import './GoalsOverview.css';

function GoalsOverview({ goals }) {
  const goalsRef = useRef([]);

  useEffect(() => {
    if (goals && goals.length > 0) {
      goalsRef.current.forEach((goalCard, index) => {
        if (goalCard) {
          const progressCircle = goalCard.querySelector('.progress-circle');
          const percentage = parseFloat(goalCard.dataset.percentage) || 0;
          
          // Animate progress circle
          const circumference = 2 * Math.PI * 45; // radius = 45
          const offset = circumference - (percentage / 100) * circumference;
          
          anime({
            targets: progressCircle.querySelector('circle:last-child'),
            strokeDashoffset: [circumference, offset],
            duration: 2000,
            delay: index * 200,
            easing: 'easeOutExpo',
          });

          // Fade in animation
          anime({
            targets: goalCard,
            opacity: [0, 1],
            scale: [0.9, 1],
            delay: index * 150,
            duration: 600,
            easing: 'easeOutExpo',
          });
        }
      });
    }
  }, [goals]);

  if (!goals || goals.length === 0) {
    return (
      <div className="goals-empty">
        <p>No financial goals set yet. Set a goal to start saving!</p>
      </div>
    );
  }

  return (
    <div className="goals-overview">
      {goals.map((goal, index) => {
        const percentage = goal.percentage || 0;
        const circumference = 2 * Math.PI * 45;
        const offset = circumference - (percentage / 100) * circumference;
        
        return (
          <div
            key={goal.id}
            ref={(el) => (goalsRef.current[index] = el)}
            data-percentage={percentage}
            className="goal-card"
          >
            <div className="goal-content">
              <h3 className="goal-name">{goal.name}</h3>
              <p className="goal-amount">
                ${goal.current_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / ${goal.target_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <p className="goal-date">
                Target: {new Date(goal.target_date).toLocaleDateString()}
              </p>
            </div>
            <div className="goal-progress">
              <svg className="progress-circle" width="100" height="100">
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="#e0e0e0"
                  strokeWidth="8"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="#667eea"
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  strokeDashoffset={circumference}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div className="progress-percentage">
                {percentage.toFixed(0)}%
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default GoalsOverview;


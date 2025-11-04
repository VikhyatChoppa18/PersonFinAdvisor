import React, { useEffect, useRef } from 'react';
import anime from 'animejs';
import './RecentTransactions.css';

function RecentTransactions({ transactions }) {
  const listRef = useRef(null);

  useEffect(() => {
    if (transactions && transactions.length > 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('.transaction-item');
      
      anime({
        targets: items,
        opacity: [0, 1],
        translateX: [-30, 0],
        delay: anime.stagger(100),
        duration: 600,
        easing: 'easeOutExpo',
      });
    }
  }, [transactions]);

  if (!transactions || transactions.length === 0) {
    return (
      <div className="transactions-empty">
        <p>No recent transactions</p>
      </div>
    );
  }

  return (
    <div className="recent-transactions" ref={listRef}>
      {transactions.map((transaction) => (
        <div key={transaction.id} className="transaction-item">
          <div className="transaction-icon">
            {transaction.amount > 0 ? '📈' : '📉'}
          </div>
          <div className="transaction-details">
            <div className="transaction-name">{transaction.name}</div>
            <div className="transaction-meta">
              {transaction.category && (
                <span className="transaction-category">{transaction.category}</span>
              )}
              <span className="transaction-date">
                {new Date(transaction.date).toLocaleDateString()}
              </span>
            </div>
          </div>
          <div
            className={`transaction-amount ${transaction.amount > 0 ? 'positive' : 'negative'}`}
          >
            {transaction.amount > 0 ? '+' : ''}
            ${Math.abs(transaction.amount).toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

export default RecentTransactions;


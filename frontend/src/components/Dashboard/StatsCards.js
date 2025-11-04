import React, { useEffect, useRef } from 'react';
import anime from 'animejs';
import './StatsCards.css';

function StatsCards({ data }) {
  const cardsRef = useRef([]);

  useEffect(() => {
    if (data) {
      // IMMEDIATELY ensure cards stay visible - no delays
      const ensureVisible = () => {
        cardsRef.current.forEach((card) => {
          if (card) {
            // Force visibility with !important
            card.style.setProperty('opacity', '1', 'important');
            card.style.setProperty('visibility', 'visible', 'important');
            card.style.setProperty('display', 'flex', 'important');
            card.style.setProperty('position', 'relative', 'important');
            card.style.setProperty('z-index', '1000', 'important');
            // Prevent any animations from hiding it
            card.style.setProperty('animation', 'none', 'important');
            card.style.setProperty('transform', 'none', 'important');
          }
        });
        // Also ensure the container is visible
        const container = document.querySelector('.stats-cards') || document.getElementById('stats-cards-container');
        if (container) {
          container.style.setProperty('opacity', '1', 'important');
          container.style.setProperty('visibility', 'visible', 'important');
          container.style.setProperty('display', 'grid', 'important');
          container.style.setProperty('animation', 'none', 'important');
        }
      };
      
      // Set visible IMMEDIATELY - no delay
      ensureVisible();
      
      // Force visibility multiple times to override any animations
      const forceVisible = () => {
        ensureVisible();
        // Also stop any anime.js animations on these elements
        cardsRef.current.forEach((card) => {
          if (card) {
            // Stop any running anime animations
            anime.remove(card);
            anime.remove(card.querySelector('.stat-value'));
            // Force visibility again
            card.style.setProperty('opacity', '1', 'important');
            card.style.setProperty('visibility', 'visible', 'important');
            card.style.setProperty('display', 'flex', 'important');
          }
        });
      };
      
      // Force visible at multiple intervals
      forceVisible();
      setTimeout(forceVisible, 10);
      setTimeout(forceVisible, 50);
      setTimeout(forceVisible, 100);
      setTimeout(forceVisible, 200);
      setTimeout(forceVisible, 500);
      
      // Set up interval to continuously ensure visibility
      const visibilityCheck = setInterval(() => {
        forceVisible();
      }, 100);
      
      // Cleanup on unmount
      return () => {
        clearInterval(visibilityCheck);
      };
    }
  }, [data]);

  if (!data) {
    console.log('StatsCards: No data provided');
    return <div className="stats-cards-loading" style={{ padding: '20px', background: 'white', borderRadius: '10px' }}>Loading stats...</div>;
  }

  // Ensure values are numbers
  const total_balance = typeof data.total_balance === 'number' ? data.total_balance : parseFloat(data.total_balance || 0);
  const total_income = typeof data.total_income === 'number' ? data.total_income : parseFloat(data.total_income || 0);
  const total_expenses = typeof data.total_expenses === 'number' ? data.total_expenses : parseFloat(data.total_expenses || 0);
  const net_income = typeof data.net_income === 'number' ? data.net_income : parseFloat(data.net_income || (total_income - total_expenses));

  console.log('StatsCards values:', { total_balance, total_income, total_expenses, net_income });
  console.log('StatsCards data object:', data);

  const stats = [
    {
      label: 'Total Balance',
      value: total_balance,
      icon: '💰',
      color: '#667eea',
    },
    {
      label: 'Monthly Income',
      value: total_income,
      icon: '📈',
      color: '#48bb78',
    },
    {
      label: 'Monthly Expenses',
      value: total_expenses,
      icon: '📉',
      color: '#f56565',
    },
    {
      label: 'Net Income',
      value: net_income,
      icon: '💵',
      color: '#ed8936',
    },
  ];

  console.log('StatsCards: Rendering', stats.length, 'cards');
  console.log('StatsCards: stats array:', stats);
  
  // Force render with explicit styles
  return (
    <div 
      className="stats-cards" 
      id="stats-cards-container"
      data-testid="stats-cards-container"
      style={{ 
        display: 'grid !important', 
        visibility: 'visible !important', 
        opacity: '1 !important', 
        width: '100% !important',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr)) !important',
        gap: '20px !important',
        marginBottom: '30px !important',
        position: 'relative !important',
        zIndex: '1000 !important',
        minHeight: '120px !important',
        background: 'transparent !important',
        padding: '0 !important',
        margin: '0 0 30px 0 !important',
        overflow: 'visible !important'
      }}
    >
      {stats.map((stat, index) => {
        const cardValue = Math.abs(stat.value);
        const formattedValue = cardValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        console.log(`Rendering stat card ${index}:`, stat.label, stat.value, formattedValue);
        
        return (
          <div
            key={`stat-${stat.label}-${index}-${stat.value}`}
            ref={(el) => {
              if (el) {
                cardsRef.current[index] = el;
                // Ensure card is visible immediately and stays visible
                el.style.setProperty('opacity', '1', 'important');
                el.style.setProperty('visibility', 'visible', 'important');
                el.style.setProperty('display', 'flex', 'important');
                el.style.setProperty('position', 'relative', 'important');
                el.style.setProperty('z-index', '1000', 'important');
                el.style.setProperty('width', '100%', 'important');
                el.style.setProperty('height', 'auto', 'important');
                el.style.setProperty('min-height', '100px', 'important');
                console.log(`Card ${index} rendered and visible:`, el, el.offsetWidth, el.offsetHeight, el.getBoundingClientRect());
              }
            }}
            className="stat-card"
            id={`stat-card-${index}`}
            data-testid={`stat-card-${index}`}
            style={{ 
              '--card-color': stat.color,
              display: 'flex !important',
              visibility: 'visible !important',
              opacity: '1 !important',
              minWidth: '250px !important',
              width: '100% !important',
              background: 'white !important',
              borderRadius: '15px !important',
              padding: '25px !important',
              boxShadow: '0 5px 15px rgba(0, 0, 0, 0.1) !important',
              borderLeft: `4px solid ${stat.color} !important`,
              alignItems: 'center !important',
              gap: '20px !important',
              position: 'relative !important',
              zIndex: '1000 !important',
              minHeight: '100px !important',
              margin: '0 !important',
              overflow: 'visible !important'
            }}
          >
            <div 
              className="stat-icon" 
              style={{ 
                fontSize: '40px', 
                width: '60px', 
                height: '60px', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              {stat.icon}
            </div>
            <div className="stat-content" style={{ flex: 1, minWidth: 0 }}>
              <div className="stat-label" style={{ color: '#666', fontSize: '14px', marginBottom: '5px', fontWeight: 500 }}>{stat.label}</div>
              <div className="stat-value" style={{ color: stat.color, fontSize: '24px', fontWeight: 700, wordBreak: 'break-word' }}>
                ${formattedValue}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default StatsCards;


import React, { useState, useEffect } from 'react';
import axios from 'axios';
import anime from 'animejs';
import './MotivationalWidget.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function MotivationalWidget() {
  const [quote, setQuote] = useState('');
  const [tip, setTip] = useState('');
  const [loading, setLoading] = useState(true);
  const widgetRef = React.useRef(null);

  useEffect(() => {
    fetchMotivation();
  }, []);

  useEffect(() => {
    if (quote && widgetRef.current) {
      // Animate quote and tip appearance
      anime({
        targets: widgetRef.current.querySelectorAll('.motivation-text'),
        opacity: [0, 1],
        translateY: [20, 0],
        delay: anime.stagger(200),
        duration: 800,
        easing: 'easeOutExpo',
      });

      // Continuous subtle animation
      anime({
        targets: widgetRef.current,
        scale: [1, 1.02, 1],
        duration: 3000,
        easing: 'easeInOutQuad',
        loop: true,
      });
    }
  }, [quote]);

  const fetchMotivation = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found');
        setQuote('Financial freedom is a journey, not a destination.');
        setTip('Start by logging in to get personalized financial motivation.');
        setLoading(false);
        return;
      }
      
      console.log('Fetching motivation from:', `${API_URL}/api/v1/agents/learning-motivation`);
      const response = await axios.post(
        `${API_URL}/api/v1/agents/learning-motivation`,
        { context: {} },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          timeout: 30000, // 30 second timeout
        }
      );
      
      console.log('Motivation response:', response.data);
      if (response.data) {
        setQuote(response.data.quote || 'Financial freedom is a journey, not a destination.');
        setTip(response.data.tip || 'Start small, stay consistent.');
      }
    } catch (error) {
      console.error('Error fetching motivation:', error);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
      } else if (error.request) {
        console.error('No response received:', error.request);
      } else {
        console.error('Error setting up request:', error.message);
      }
      // Fallback quotes - don't fail if Ollama is down
      setQuote('The best time to plant a tree was 20 years ago. The second best time is now.');
      setTip('Automate your savings by setting up automatic transfers to a savings account each month.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="motivational-widget">
        <div className="loading">Loading motivation...</div>
      </div>
    );
  }

  return (
    <div ref={widgetRef} className="motivational-widget">
      <div className="motivation-icon">💪</div>
      <div className="motivation-content">
        <div className="motivation-quote motivation-text">
          "{quote}"
        </div>
        <div className="motivation-tip motivation-text">
          💡 Tip: {tip}
        </div>
      </div>
      <button className="refresh-button" onClick={fetchMotivation}>
        🔄 New Motivation
      </button>
    </div>
  );
}

export default MotivationalWidget;


import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import anime from 'animejs';
import './FinancialAdvisor.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function FinancialAdvisor() {
  const [healthScore, setHealthScore] = useState(null);
  const [optimization, setOptimization] = useState(null);
  const [question, setQuestion] = useState('');
  const [advice, setAdvice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [loadingOptimization, setLoadingOptimization] = useState(false);

  useEffect(() => {
    fetchFinancialHealth();
    fetchOptimization();
  }, []);

  useEffect(() => {
    if (healthScore) {
      anime({
        targets: '.health-score-circle',
        scale: [0, 1],
        duration: 1000,
        easing: 'easeOutElastic(1, .6)',
      });
    }
  }, [healthScore]);

  const fetchFinancialHealth = async () => {
    setLoadingHealth(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found');
        toast.error('Please log in to view financial health score');
        setLoadingHealth(false);
        return;
      }
      
      console.log('Fetching financial health from:', `${API_URL}/api/v1/agents/financial-health`);
      const response = await axios.get(`${API_URL}/api/v1/agents/financial-health`, {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        timeout: 30000, // 30 second timeout
      });
      
      console.log('Financial health response:', response.data);
      setHealthScore(response.data);
    } catch (error) {
      console.error('Error fetching financial health:', error);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
        toast.error(`Failed to fetch financial health score: ${error.response.status}`);
      } else if (error.request) {
        console.error('No response received:', error.request);
        toast.error('Unable to connect to server. Please check if the backend is running.');
      } else {
        console.error('Error setting up request:', error.message);
        toast.error(`Failed to fetch financial health score: ${error.message}`);
      }
      // Set fallback health score so UI still shows something
      setHealthScore({
        score: 70,
        health_status: "Good",
        issues: [],
        recommendations: [
          "Continue tracking your expenses",
          "Aim for 20% savings rate",
          "Build 3-6 months emergency fund"
        ]
      });
    } finally {
      setLoadingHealth(false);
    }
  };

  const fetchOptimization = async () => {
    setLoadingOptimization(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found');
        toast.error('Please log in to view optimization recommendations');
        setLoadingOptimization(false);
        return;
      }
      
      console.log('Fetching optimization recommendations from:', `${API_URL}/api/v1/agents/optimize-spending`);
      const response = await axios.get(`${API_URL}/api/v1/agents/optimize-spending`, {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        timeout: 30000, // 30 second timeout
      });
      
      console.log('Optimization response:', response.data);
      setOptimization(response.data);
    } catch (error) {
      console.error('Error fetching optimization:', error);
      if (error.response) {
        // Server responded with error status
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
        toast.error(`Failed to fetch optimization recommendations: ${error.response.status}`);
      } else if (error.request) {
        // Request made but no response received
        console.error('No response received:', error.request);
        toast.error('Unable to connect to server. Please check if the backend is running.');
      } else {
        // Error setting up request
        console.error('Error setting up request:', error.message);
        toast.error(`Failed to fetch optimization recommendations: ${error.message}`);
      }
      // Set fallback optimization data so UI still shows something
      setOptimization({
        spending_optimization: [
          "Review top spending categories and identify areas to cut back",
          "Consider meal planning to reduce food expenses",
          "Cancel unused subscriptions"
        ],
        savings_opportunities: [
          "Automate savings transfers",
          "Consider high-yield savings accounts"
        ],
        priority_actions: [
          "Set up automatic savings",
          "Review and cancel unnecessary subscriptions"
        ]
      });
    } finally {
      setLoadingOptimization(false);
    }
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No authentication token found');
        toast.error('Please log in to ask questions');
        setLoading(false);
        return;
      }
      
      console.log('Asking question:', question);
      const response = await axios.post(
        `${API_URL}/api/v1/agents/financial-advice`,
        null,
        {
          params: {
            question: question
          },
          headers: {
            'Authorization': `Bearer ${token}`
          },
          timeout: 60000, // 60 second timeout for LLM responses
        }
      );
      
      console.log('Advice response:', response.data);
      setAdvice(response.data);
      setQuestion('');
    } catch (error) {
      console.error('Error getting advice:', error);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
        toast.error(`Failed to get financial advice: ${error.response.status}`);
      } else if (error.request) {
        console.error('No response received:', error.request);
        toast.error('Unable to connect to server. Please check if the backend is running.');
      } else {
        console.error('Error setting up request:', error.message);
        toast.error(`Failed to get financial advice: ${error.message}`);
      }
      // Set fallback advice so user gets some response
      setAdvice({
        answer: `I apologize, but I'm experiencing technical difficulties right now. Your question was: "${question}". Please try asking again in a moment.`,
        recommendations: [
          "Try asking your question again",
          "Check your financial dashboard for insights",
          "Review your budget and goals"
        ],
        next_steps: [
          "Retry your question",
          "Explore the dashboard for more information"
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#48bb78';
    if (score >= 60) return '#ed8936';
    if (score >= 40) return '#fbbf24';
    return '#f56565';
  };

  return (
    <div className="financial-advisor">
      <h2>Personal Finance Advisor</h2>
      
      {/* Financial Health Score */}
      {loadingHealth ? (
        <div className="loading">Loading health score...</div>
      ) : (
        <div className="health-score-card">
          <h3>Financial Health Score</h3>
          {healthScore ? (
            <>
              <div className="health-score-display">
                <div className="health-score-circle" style={{ '--score-color': getScoreColor(healthScore.score) }}>
                  <div className="score-value">{healthScore.score}</div>
                  <div className="score-status">{healthScore.health_status}</div>
                </div>
              </div>
              
              {healthScore.issues && healthScore.issues.length > 0 && (
                <div className="issues-section">
                  <h4>⚠️ Issues</h4>
                  <ul>
                    {healthScore.issues.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {healthScore.recommendations && healthScore.recommendations.length > 0 && (
                <div className="recommendations-section">
                  <h4>💡 Recommendations</h4>
                  <ul>
                    {healthScore.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <div className="section">
              <p>Loading financial health score...</p>
            </div>
          )}
        </div>
      )}

      {/* Spending Optimization */}
      {loadingOptimization ? (
        <div className="loading">Loading optimization recommendations...</div>
      ) : (
        <div className="optimization-card">
          <h3>Spending Optimization</h3>
          
          {optimization ? (
            <>
              {optimization.spending_optimization && optimization.spending_optimization.length > 0 && (
                <div className="section">
                  <h4>💰 Ways to Reduce Spending</h4>
                  <ul>
                    {optimization.spending_optimization.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {optimization.savings_opportunities && optimization.savings_opportunities.length > 0 && (
                <div className="section">
                  <h4>💵 Savings Opportunities</h4>
                  <ul>
                    {optimization.savings_opportunities.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {optimization.priority_actions && optimization.priority_actions.length > 0 && (
                <div className="section priority">
                  <h4>🎯 Priority Actions</h4>
                  <ol>
                    {optimization.priority_actions.map((action, idx) => (
                      <li key={idx}>{action}</li>
                    ))}
                  </ol>
                </div>
              )}
              
              {(!optimization.spending_optimization || optimization.spending_optimization.length === 0) &&
               (!optimization.savings_opportunities || optimization.savings_opportunities.length === 0) &&
               (!optimization.priority_actions || optimization.priority_actions.length === 0) && (
                <div className="section">
                  <p>No optimization recommendations available at this time.</p>
                </div>
              )}
            </>
          ) : (
            <div className="section">
              <p>Loading optimization recommendations...</p>
            </div>
          )}
        </div>
      )}

      {/* Ask Financial Advisor */}
      <div className="advisor-chat">
        <h3>Ask Your Financial Advisor</h3>
        <form onSubmit={handleAskQuestion}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your finances..."
            className="question-input"
          />
          <button type="submit" className="btn-ask" disabled={loading || !question.trim()}>
            {loading ? 'Asking...' : 'Ask'}
          </button>
        </form>
        
        {advice && (
          <div className="advice-response">
            {advice.answer && (
              <div className="answer">
                <strong>Answer:</strong>
                <p style={{ whiteSpace: 'pre-line' }}>{advice.answer}</p>
              </div>
            )}
            
            {/* Stock Recommendations */}
            {advice.stock_recommendations && advice.stock_recommendations.length > 0 && (
              <div className="stock-recommendations">
                <strong>📈 Stock Recommendations:</strong>
                <div className="stocks-grid">
                  {advice.stock_recommendations.map((stock, idx) => (
                    <div key={idx} className="stock-card">
                      <div className="stock-header">
                        <h4>{stock.symbol}</h4>
                        <span className={`recommendation-badge ${stock.recommendation?.toLowerCase()}`}>
                          {stock.recommendation || 'HOLD'}
                        </span>
                      </div>
                      <div className="stock-name">{stock.name || stock.symbol}</div>
                      <div className="stock-price">${stock.current_price?.toFixed(2) || 'N/A'}</div>
                      {stock.price_change_52w !== undefined && (
                        <div className={`stock-change ${stock.price_change_52w >= 0 ? 'positive' : 'negative'}`}>
                          {stock.price_change_52w >= 0 ? '+' : ''}{stock.price_change_52w?.toFixed(2)}% (52w)
                        </div>
                      )}
                      {stock.reasons && stock.reasons.length > 0 && (
                        <div className="stock-reasons">
                          <strong>Why:</strong>
                          <ul>
                            {stock.reasons.slice(0, 2).map((reason, rIdx) => (
                              <li key={rIdx}>{reason}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {stock.market_context?.why_recommended && (
                        <div className="stock-context">
                          <small>{stock.market_context.why_recommended}</small>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {advice.recommendations && advice.recommendations.length > 0 && (
              <div className="recommendations">
                <strong>Recommendations:</strong>
                <ul>
                  {advice.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
            {advice.next_steps && advice.next_steps.length > 0 && (
              <div className="next-steps">
                <strong>Next Steps:</strong>
                <ul>
                  {advice.next_steps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default FinancialAdvisor;


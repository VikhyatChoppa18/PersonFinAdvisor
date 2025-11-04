import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import anime from 'animejs';
import StatsCards from './StatsCards';
import BudgetProgress from './BudgetProgress';
import GoalsOverview from './GoalsOverview';
import RecentTransactions from './RecentTransactions';
import FinancialChart from './FinancialChart';
import MotivationalWidget from './MotivationalWidget';
import CreateBudget from './CreateBudget';
import CreateGoal from './CreateGoal';
import FinancialAdvisor from './FinancialAdvisor';
import './Dashboard.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function Dashboard() {
  const { logout } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCreateBudget, setShowCreateBudget] = useState(false);
  const [showCreateGoal, setShowCreateGoal] = useState(false);

  useEffect(() => {
    fetchDashboardData();
    
    // Animate dashboard on load (but exclude stats cards)
    anime({
      targets: '.dashboard-container',
      opacity: [0, 1],
      duration: 800,
      easing: 'easeOutExpo',
    });

    // Animate dashboard cards but NOT stats cards - explicitly exclude them
    anime({
      targets: '.dashboard-card:not(.stat-card):not(.stats-cards)',
      opacity: [0, 1],
      translateY: [30, 0],
      delay: anime.stagger(100),
      duration: 600,
      easing: 'easeOutExpo',
    });
    
    // IMMEDIATELY ensure stats cards stay visible and NEVER animate them
    const ensureStatsVisible = () => {
      const statsCards = document.querySelectorAll('.stat-card, .stats-cards, #stats-cards-container');
      statsCards.forEach((card) => {
        if (card) {
          // Stop any anime.js animations
          anime.remove(card);
          // Force visibility with !important
          card.style.setProperty('opacity', '1', 'important');
          card.style.setProperty('visibility', 'visible', 'important');
          if (card.classList.contains('stat-card')) {
            card.style.setProperty('display', 'flex', 'important');
          } else {
            card.style.setProperty('display', 'grid', 'important');
          }
          card.style.setProperty('animation', 'none', 'important');
          card.style.setProperty('transform', 'none', 'important');
        }
      });
    };
    
    // Force visible IMMEDIATELY and repeatedly
    ensureStatsVisible();
    setTimeout(ensureStatsVisible, 10);
    setTimeout(ensureStatsVisible, 50);
    setTimeout(ensureStatsVisible, 100);
    setTimeout(ensureStatsVisible, 200);
    setTimeout(ensureStatsVisible, 500);
    setTimeout(ensureStatsVisible, 1000);
    
    // Continuous check to ensure they stay visible
    const statsVisibilityCheck = setInterval(() => {
      ensureStatsVisible();
    }, 200);
    
    // Cleanup
    return () => {
      clearInterval(statsVisibilityCheck);
    };
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.error('No token found in localStorage');
        setLoading(false);
        return;
      }
      
      console.log('Fetching dashboard data from:', `${API_URL}/api/v1/dashboard/`);
      const response = await axios.get(`${API_URL}/api/v1/dashboard/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Dashboard data received:', response.data);
      console.log('Budgets count:', response.data.budgets?.length || 0);
      console.log('Goals count:', response.data.goals?.length || 0);
      console.log('Transactions count:', response.data.recent_transactions?.length || 0);
      
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      console.error('Error status:', error.response?.status);
      console.error('Error details:', error.response?.data);
      console.error('Error message:', error.message);
      
      // If 401, token might be invalid - user needs to login again
      if (error.response?.status === 401) {
        console.error('Authentication failed - user needs to login again');
        localStorage.removeItem('token');
        logout();
      }
      
      setLoading(false);
      // Set empty data structure to prevent crashes
      setDashboardData({
        budgets: [],
        goals: [],
        recent_transactions: [],
        total_balance: 0,
        total_income: 0,
        total_expenses: 0,
        net_income: 0,
        unread_alerts: 0
      });
    }
  };

  const handleBudgetCreated = () => {
    setShowCreateBudget(false);
    fetchDashboardData(); // Refresh dashboard data
  };

  const handleGoalCreated = () => {
    setShowCreateGoal(false);
    fetchDashboardData(); // Refresh dashboard data
  };

  const handleLogout = () => {
    logout();
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading your financial dashboard...</p>
      </div>
    );
  }

  // Ensure dashboardData is not null
  if (!dashboardData) {
    return (
      <div className="dashboard-loading">
        <p>No data available. Please refresh.</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Personal Finance AI</h1>
          <nav className="dashboard-nav">
            <button
              className={activeTab === 'overview' ? 'active' : ''}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={activeTab === 'budgets' ? 'active' : ''}
              onClick={() => setActiveTab('budgets')}
            >
              Budgets
            </button>
            <button
              className={activeTab === 'goals' ? 'active' : ''}
              onClick={() => setActiveTab('goals')}
            >
              Goals
            </button>
            <button
              className={activeTab === 'advisor' ? 'active' : ''}
              onClick={() => setActiveTab('advisor')}
            >
              Financial Advisor
            </button>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </nav>
        </div>
      </header>

      <div className="dashboard-container" style={{ position: 'relative', zIndex: 1 }}>
        {activeTab === 'overview' && dashboardData && (
          <>
            {/* Stats Cards - Always render if data exists */}
            {dashboardData.total_balance !== undefined && dashboardData.total_balance !== null && (
              <div 
                style={{ 
                  position: 'relative', 
                  zIndex: 1000, 
                  width: '100%', 
                  marginBottom: '30px',
                  display: 'block',
                  visibility: 'visible',
                  opacity: 1,
                  minHeight: '120px',
                  background: 'transparent'
                }}
              >
                <StatsCards data={dashboardData} />
              </div>
            )}
            <div className="dashboard-grid">
              <div className="dashboard-card">
                <h2>Budget Progress</h2>
                {dashboardData.budgets && dashboardData.budgets.length > 0 ? (
                  <BudgetProgress budgets={dashboardData.budgets} />
                ) : (
                  <div className="empty-state">
                    <p>No budgets set yet. Create a budget to start tracking!</p>
                  </div>
                )}
              </div>
              <div className="dashboard-card">
                <h2>Financial Overview</h2>
                <FinancialChart data={dashboardData} />
              </div>
            </div>
            <div className="dashboard-grid">
              <div className="dashboard-card">
                <h2>Goals</h2>
                {dashboardData.goals && dashboardData.goals.length > 0 ? (
                  <GoalsOverview goals={dashboardData.goals} />
                ) : (
                  <div className="empty-state">
                    <p>No goals set yet. Set a financial goal to start saving!</p>
                  </div>
                )}
              </div>
              <div className="dashboard-card">
                <h2>Motivation</h2>
                <MotivationalWidget />
              </div>
            </div>
            <div className="dashboard-card">
              <h2>Recent Transactions</h2>
              <RecentTransactions transactions={dashboardData.recent_transactions || []} />
            </div>
          </>
        )}

        {activeTab === 'budgets' && (
          <div className="budgets-section">
            <div className="dashboard-card">
              <div className="card-header">
                <h2>Budget Management</h2>
                <button 
                  className="btn-create" 
                  onClick={() => setShowCreateBudget(!showCreateBudget)}
                >
                  {showCreateBudget ? 'Cancel' : '+ Create Budget'}
                </button>
              </div>
              {showCreateBudget && (
                <CreateBudget 
                  onBudgetCreated={handleBudgetCreated}
                  onCancel={() => setShowCreateBudget(false)}
                />
              )}
              <BudgetProgress budgets={dashboardData?.budgets || []} />
            </div>
          </div>
        )}

        {activeTab === 'goals' && (
          <div className="goals-section">
            <div className="dashboard-card">
              <div className="card-header">
                <h2>Financial Goals</h2>
                <button 
                  className="btn-create" 
                  onClick={() => setShowCreateGoal(!showCreateGoal)}
                >
                  {showCreateGoal ? 'Cancel' : '+ Create Goal'}
                </button>
              </div>
              {showCreateGoal && (
                <CreateGoal 
                  onGoalCreated={handleGoalCreated}
                  onCancel={() => setShowCreateGoal(false)}
                />
              )}
              <GoalsOverview goals={dashboardData?.goals || []} />
            </div>
          </div>
        )}

        {activeTab === 'advisor' && (
          <div className="advisor-section">
            <div className="dashboard-card">
              <FinancialAdvisor />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;


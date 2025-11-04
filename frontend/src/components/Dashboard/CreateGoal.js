import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import './CreateBudget.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function CreateGoal({ onGoalCreated, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    target_amount: '',
    target_date: new Date(new Date().setMonth(new Date().getMonth() + 6)).toISOString().split('T')[0],
    goal_type: 'savings',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name || formData.name.trim() === '') {
      newErrors.name = 'Goal name is required';
    }
    
    if (!formData.target_amount || formData.target_amount === '') {
      newErrors.target_amount = 'Target amount is required';
    } else if (parseFloat(formData.target_amount) <= 0) {
      newErrors.target_amount = 'Target amount must be greater than 0';
    } else if (isNaN(parseFloat(formData.target_amount))) {
      newErrors.target_amount = 'Target amount must be a valid number';
    }
    
    if (!formData.target_date) {
      newErrors.target_date = 'Target date is required';
    } else if (new Date(formData.target_date) <= new Date()) {
      newErrors.target_date = 'Target date must be in the future';
    }
    
    if (!formData.goal_type) {
      newErrors.goal_type = 'Goal type is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
      toast.error('Please fix the validation errors');
      return;
    }
    
    setLoading(true);
    setErrors({});

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        toast.error('Please login again');
        return;
      }

      const targetDate = new Date(formData.target_date + 'T00:00:00Z');
      const targetAmount = parseFloat(formData.target_amount);
      
      if (isNaN(targetAmount) || targetAmount <= 0) {
        toast.error('Please enter a valid target amount');
        setLoading(false);
        return;
      }

      const payload = {
        name: formData.name.trim(),
        target_amount: targetAmount,
        target_date: targetDate.toISOString(),
        goal_type: formData.goal_type,
      };

      console.log('Sending goal data:', payload);

      const response = await axios.post(
        `${API_URL}/api/v1/goals/`,
        payload,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      toast.success('Goal created successfully!');
      if (onGoalCreated) {
        onGoalCreated(response.data);
      }
      
      // Reset form
      setFormData({
        name: '',
        target_amount: '',
        target_date: new Date(new Date().setMonth(new Date().getMonth() + 6)).toISOString().split('T')[0],
        goal_type: 'savings',
      });
      setErrors({});
    } catch (error) {
      console.error('Error creating goal:', error);
      console.error('Error response:', error.response?.data);
      
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
      } else if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Validation errors from FastAPI
          const validationErrors = error.response.data.detail;
          const newErrors = {};
          validationErrors.forEach(err => {
            if (err.loc && err.loc.length > 1) {
              newErrors[err.loc[1]] = err.msg;
            }
          });
          setErrors(newErrors);
          toast.error('Please fix the validation errors');
        } else {
          toast.error(error.response.data.detail);
        }
      } else {
        toast.error('Failed to create goal. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="create-budget-form">
      <h3>Create New Financial Goal</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Goal Name</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="e.g., Emergency Fund, Vacation, House Down Payment"
            className={errors.name ? 'error' : ''}
            required
          />
          {errors.name && <span className="error-message">{errors.name}</span>}
        </div>

        <div className="form-group">
          <label>Target Amount ($)</label>
          <input
            type="number"
            name="target_amount"
            value={formData.target_amount}
            onChange={handleChange}
            placeholder="0.00"
            step="0.01"
            min="0"
            className={errors.target_amount ? 'error' : ''}
            required
          />
          {errors.target_amount && <span className="error-message">{errors.target_amount}</span>}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Target Date</label>
            <input
              type="date"
              name="target_date"
              value={formData.target_date}
              onChange={handleChange}
              className={errors.target_date ? 'error' : ''}
              required
            />
            {errors.target_date && <span className="error-message">{errors.target_date}</span>}
          </div>

          <div className="form-group">
            <label>Goal Type</label>
            <select
              name="goal_type"
              value={formData.goal_type}
              onChange={handleChange}
              className={errors.goal_type ? 'error' : ''}
              required
            >
              <option value="savings">Savings</option>
              <option value="investment">Investment</option>
              <option value="debt_payoff">Debt Payoff</option>
            </select>
            {errors.goal_type && <span className="error-message">{errors.goal_type}</span>}
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Goal'}
          </button>
          {onCancel && (
            <button type="button" className="btn-secondary" onClick={onCancel}>
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

export default CreateGoal;


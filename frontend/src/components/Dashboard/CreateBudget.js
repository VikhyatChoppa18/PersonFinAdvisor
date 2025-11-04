import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import anime from 'animejs';
import './CreateBudget.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function CreateBudget({ onBudgetCreated, onCancel }) {
  const [formData, setFormData] = useState({
    category: '',
    amount: '',
    period: 'monthly',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(new Date().setMonth(new Date().getMonth() + 1)).toISOString().split('T')[0],
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.category || formData.category.trim() === '') {
      newErrors.category = 'Category is required';
    }
    
    if (!formData.amount || formData.amount === '') {
      newErrors.amount = 'Amount is required';
    } else if (parseFloat(formData.amount) <= 0) {
      newErrors.amount = 'Amount must be greater than 0';
    } else if (isNaN(parseFloat(formData.amount))) {
      newErrors.amount = 'Amount must be a valid number';
    }
    
    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }
    
    if (!formData.end_date) {
      newErrors.end_date = 'End date is required';
    } else if (formData.start_date && new Date(formData.end_date) <= new Date(formData.start_date)) {
      newErrors.end_date = 'End date must be after start date';
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

      const startDate = new Date(formData.start_date + 'T00:00:00Z');
      const endDate = new Date(formData.end_date + 'T23:59:59Z');
      
      const amount = parseFloat(formData.amount);
      if (isNaN(amount) || amount <= 0) {
        toast.error('Please enter a valid amount');
        setLoading(false);
        return;
      }

      const payload = {
        category: formData.category.trim(),
        amount: amount,
        period: formData.period,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      };

      console.log('Sending budget data:', payload);

      const response = await axios.post(
        `${API_URL}/api/v1/budgets/`,
        payload,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      toast.success('Budget created successfully!');
      if (onBudgetCreated) {
        onBudgetCreated(response.data);
      }
      
      // Reset form
      setFormData({
        category: '',
        amount: '',
        period: 'monthly',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date(new Date().setMonth(new Date().getMonth() + 1)).toISOString().split('T')[0],
      });
      setErrors({});
    } catch (error) {
      console.error('Error creating budget:', error);
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
        toast.error('Failed to create budget. Please try again.');
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
      <h3>Create New Budget</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Category</label>
          <input
            type="text"
            name="category"
            value={formData.category}
            onChange={handleChange}
            placeholder="e.g., Food & Dining, Shopping, Transportation"
            className={errors.category ? 'error' : ''}
            required
          />
          {errors.category && <span className="error-message">{errors.category}</span>}
        </div>

        <div className="form-group">
          <label>Budget Amount ($)</label>
          <input
            type="number"
            name="amount"
            value={formData.amount}
            onChange={handleChange}
            placeholder="0.00"
            step="0.01"
            min="0"
            className={errors.amount ? 'error' : ''}
            required
          />
          {errors.amount && <span className="error-message">{errors.amount}</span>}
        </div>

        <div className="form-group">
          <label>Period</label>
          <select
            name="period"
            value={formData.period}
            onChange={handleChange}
            required
          >
            <option value="monthly">Monthly</option>
            <option value="weekly">Weekly</option>
            <option value="yearly">Yearly</option>
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Start Date</label>
            <input
              type="date"
              name="start_date"
              value={formData.start_date}
              onChange={handleChange}
              className={errors.start_date ? 'error' : ''}
              required
            />
            {errors.start_date && <span className="error-message">{errors.start_date}</span>}
          </div>

          <div className="form-group">
            <label>End Date</label>
            <input
              type="date"
              name="end_date"
              value={formData.end_date}
              onChange={handleChange}
              className={errors.end_date ? 'error' : ''}
              required
            />
            {errors.end_date && <span className="error-message">{errors.end_date}</span>}
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Budget'}
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

export default CreateBudget;


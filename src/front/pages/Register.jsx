import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom';

const backendUrl = import.meta.env.VITE_BACKEND_URL;

const Register = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: '',
    password: '',
    image: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    const { name, value, type, files } = e.target;
    if (type === 'file') {
      setForm({ ...form, [name]: files[0] });
    } else {
      setForm({ ...form, [name]: value });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    const data = new FormData();
    data.append('email', form.email);
    data.append('password', form.password);
    if (form.image) data.append('image', form.image);

    try {
      const res = await fetch(`${backendUrl}/register`, {
        method: 'POST',
        body: data
      });
      const result = await res.json();
      if (!res.ok) {
        setError(result.error || 'Error registering user');
      } else {
        setSuccess(result.message || 'User registered successfully');
        setForm({ email: '', password: '', image: null });
        setTimeout(() => {
          navigate('/login');
        }, 2000); // Redirect after 2 seconds
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-5" style={{ maxWidth: 500 }}>
      <div className="card shadow p-4">
        <div className="card-body">
          <h2 className="card-title mb-4 text-center">Register</h2>
          <form onSubmit={handleSubmit} encType="multipart/form-data">
            <div className="mb-3">
              <label className="form-label">Email:</label>
              <input
                type="email"
                name="email"
                className="form-control"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Password:</label>
              <input
                type="password"
                name="password"
                className="form-control"
                value={form.password}
                onChange={handleChange}
                minLength={6}
                required
              />
            </div>
            <div className="mb-5">
              <label className="form-label">Profile Image (optional):</label>
              <input
                type="file"
                name="image"
                className="form-control"
                accept=".png,.jpg,.jpeg"
                onChange={handleChange}
              />
            </div>
            <button type="submit" className="btn btn-primary w-100" disabled={loading}>
              {loading ? 'Registering...' : 'Register'}
            </button>
            {error && <div className="alert alert-danger mt-3">{error}</div>}
            {success && <div className="alert alert-success mt-3">{success}</div>}
          </form>
        </div>
      </div>
    </div>
  );
};

export default Register
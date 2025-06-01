import React, { useEffect } from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import useGlobalReducer from '../hooks/useGlobalReducer'

const DashLayout = () => {
    const { store } = useGlobalReducer();
    const navigate = useNavigate();

    useEffect(() => {
        if (!store.user) {
            navigate('/login', { replace: true }); // Redirect to login if not authenticated, replace history to prevent going back
        }
    }, [store.user]);

  return (
    <div className="d-flex flex-column flex-md-row h-md-full bg-light">
        {/* SideBar */}
        <div className="bg-white border-right col-3" style={{ width: '250px' }}>
            <h2 className="p-3">Dashboard</h2>
            <ul className="nav flex-column">
                <li className="nav-item">
                    <Link className="nav-link active" to="/products">Product Table</Link>
                </li>
                <li className="nav-item">
                    <Link className="nav-link" to="/products/new">Add Product</Link>
                </li>
            </ul>
        </div>

        {/* Main Panel */}
        <div className="col-9 p-4">
            <Outlet/>
        </div>
    </div>
  )
}

export default DashLayout
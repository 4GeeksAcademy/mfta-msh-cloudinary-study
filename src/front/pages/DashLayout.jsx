import React from 'react'
import { Link, Outlet } from 'react-router-dom'

const DashLayout = () => {
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
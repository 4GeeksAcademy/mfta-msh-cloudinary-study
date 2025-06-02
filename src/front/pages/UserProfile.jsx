import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useGlobalReducer from '../hooks/useGlobalReducer'

const backendUrl = import.meta.env.VITE_BACKEND_URL

const UserProfile = () => {
  const { store } = useGlobalReducer()
  const navigate = useNavigate()
  console.log("user: ", store.user)

  useEffect(() => {
    if (!store.user) {
      navigate('/login', { replace: true })
      return
    }
  }, [store.user, navigate])

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-8 col-lg-6">
          <div className="card shadow-lg border-0 rounded-4">
            <div className="card-body text-center p-5">
              <div className="mb-4">
                <img
                  src={store.user?.picture_url}
                  alt="Foto de perfil"
                  className="rounded-circle border border-1 border-white"
                  style={{ width: 200, height: 200, objectFit: 'cover', boxShadow: '0 4px 24px rgba(0,0,0,0.1)' }}
                />
              </div>
              <h6 className="text-muted mb-3">{store.user?.email}</h6>
              <div className="mb-3">
                <span className="badge bg-light fs-6 text-secondary">{store.user?.role || 'Usuario'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserProfile
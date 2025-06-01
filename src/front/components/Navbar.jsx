import { Link } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer";

export const Navbar = () => {
	const { store, dispatch } = useGlobalReducer();

	const handleLogout = () => {
		localStorage.removeItem("token");
		dispatch({ type: "logout" });
	}

	return (
		<nav className="navbar navbar-light bg-light">
			<div className="container">
				<Link to="/">
					<span className="navbar-brand mb-0 h1">React Boilerplate</span>
				</Link>

				<div className="ml-auto">
					{store.user ? (
						<>
							<span className="navbar-text me-3">
								Welcome, {store.user.email}
							</span>
							<Link to="/products" className="btn btn-secondary me-2">
								Products
							</Link>
							<Link to="/profile" className="btn btn-secondary me-2">
								Profile
							</Link>
							<button className="btn btn-danger" onClick={handleLogout}>
								Logout
							</button>
						</>
					) : (
						<>
							<Link to="/login" className="btn btn-primary me-2">
								Login
							</Link>
							<Link to="/register" className="btn btn-primary">
								Register
							</Link>
						</>
					)}


				</div>
			</div>
		</nav>
	);
};
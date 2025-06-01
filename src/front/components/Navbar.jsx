import { Link } from "react-router-dom";

export const Navbar = () => {

	return (
		<nav className="navbar navbar-light bg-light">
			<div className="container">
				<Link to="/">
					<span className="navbar-brand mb-0 h1">React Boilerplate</span>
				</Link>
				<div className="ml-auto">
					<Link to="/login" className="btn btn-success me-2">
						Login
					</Link>
					<Link to="/register" className="btn btn-primary">
						Register
					</Link>
				</div>
			</div>
		</nav>
	);
};
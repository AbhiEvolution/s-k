import { Navigate, Outlet, useLocation } from "react-router";
import { useSelector } from "react-redux";

function ProtectedRoute() {
  const location = useLocation();
  const accessToken = useSelector((state) => state.auth.accessToken);

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
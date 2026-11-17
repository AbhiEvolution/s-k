import { Navigate, Outlet, useLocation } from "react-router";
import { useSelector } from "react-redux";
import AppProvider from "../context/AppProvider";
import AppHeader from "./AppHeader";

function ProtectedRoute() {
  const location = useLocation();
  const accessToken = useSelector((state) => state.auth.accessToken);

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // Everything behind the login shares one header and one copy of "my clinics".
  return (
    <AppProvider>
      <AppHeader />
      <Outlet />
    </AppProvider>
  );
}

export default ProtectedRoute;

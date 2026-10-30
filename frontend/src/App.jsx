import { Navigate, Route, Routes } from "react-router";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Patients from "./pages/Patients";
import Register from "./pages/Register";
import ProtectedRoute from "./components/ProtectedRoute";
import NewPatient from "./pages/patients/NewPatient";
import ShowPatient from "./pages/patients/ShowPatient";
import EditPatient from "./pages/patients/EditPatient";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/patients" element={<Patients />} />
        <Route path="/patient/new" element={<NewPatient />}/>
        <Route path="/patients/:id" element={<ShowPatient />} />
        <Route path="/patients/:id/edit" element={<EditPatient />} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;

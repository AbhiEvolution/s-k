import { Link } from 'react-router'
import { formatWhen } from '../lib/format'
import { StatusBadge } from './ui'

/** One table for every list of appointments (the main list and a patient's history). */
export default function AppointmentsTable({
  items,
  patientName,
  doctorName,
  onCancel,
  cancellingId,
  showPatient = true,
}) {
  return (
    <div className="overflow-x-auto">
      <table className="data-table">
        <thead>
          <tr>
            <th>When</th>
            {showPatient && <th>Patient</th>}
            <th>Doctor</th>
            <th>Status</th>
            <th className="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((appointment) => (
            <tr key={appointment.id}>
              <td className="whitespace-nowrap">{formatWhen(appointment.starts_at)}</td>
              {showPatient && (
                <td>
                  <Link to={`/patients/${appointment.patient_id}`} className="link">
                    {patientName(appointment.patient_id)}
                  </Link>
                </td>
              )}
              <td>{doctorName(appointment.doctor_id)}</td>
              <td><StatusBadge value={appointment.status} /></td>
              <td className="whitespace-nowrap text-right">
                {appointment.status === 'booked' && (
                  <button
                    type="button"
                    onClick={() => onCancel(appointment)}
                    disabled={cancellingId === appointment.id}
                    className="button-danger button-sm"
                  >
                    {cancellingId === appointment.id ? 'Cancelling...' : 'Cancel'}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

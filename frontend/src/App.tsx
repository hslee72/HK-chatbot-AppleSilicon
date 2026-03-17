import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ChatScreen from './screens/Chat';
import DocumentsScreen from './screens/Documents';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/chat" element={<ChatScreen />} />
        <Route path="/documents" element={<DocumentsScreen />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

import React, { useContext, useState } from 'react';
import api from '../api';
import { AuthContext } from '../context/AuthContext';
import { useForm } from '../hooks/useForm';
import { useToast } from '../hooks/useToast';
import { ToastContainer } from '../components/ToastContainer';

export const ProfilePage = () => {
  const { user, updateUser } = useContext(AuthContext);
  const { toasts, addToast } = useToast();
  const { values, handleChange } = useForm({
    name: user?.name || '',
    password: ''
  });
  const [avatarFile, setAvatarFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  // Function to create preview URL on file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAvatarFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      await api.put('/me', values);
      updateUser({ ...user, name: values.name });
      addToast('Profile details updated!', 'success');
    } catch (err) {
      addToast('Profile update failed', 'error');
    }
  };

  const handleAvatarUpload = async () => {
    if (!avatarFile) return;
    const formData = new FormData();
    formData.append('avatar', avatarFile);

    try {
      const res = await api.post('/upload-avatar', formData);
      updateUser({ ...user, avatar_url: res.data.avatar_url });
      addToast('Avatar uploaded!', 'success');
      setPreviewUrl(null); // Clear preview after upload
    } catch (err) {
      addToast('Avatar upload failed', 'error');
    }
  };

  // Image Source Priority: Preview URL > DB Avatar URL > Placeholder
  const getImageSource = () => {
    if (previewUrl) return previewUrl;
    if (user?.avatar_url) return `http://localhost:5000${user.avatar_url}`;
    return 'https://via.placeholder.com/120';
  };

  return (
    <div className="page-container">
      <ToastContainer toasts={toasts} />
      <h2 className="page-title">User Profile Settings</h2>
      
      <div className="card">
        <h3>Avatar Image</h3>
        <div className="avatar-preview-section">
          <img
            src={getImageSource()}
            alt="User Avatar"
            className="large-avatar"
          />
          <input type="file" accept="image/*" onChange={handleFileChange} />
          <button onClick={handleAvatarUpload} className="btn-primary">
            Upload New Avatar
          </button>
        </div>
      </div>

      <div className="card">
        <h3>Account Credentials</h3>
        <form onSubmit={handleProfileUpdate} className="form-column">
          <div className="form-group">
            <label>Name</label>
            <input name="name" value={values.name} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label>New Password (leave blank to keep current)</label>
            <input name="password" type="password" value={values.password} onChange={handleChange} />
          </div>
          <button type="submit" className="btn-primary">Save Profile Changes</button>
        </form>
      </div>
    </div>
  );
};

export default ProfilePage;
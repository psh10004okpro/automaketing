import { useState, useEffect } from 'react';
import { smsAPI } from '../services/api';

interface SMSCampaign {
  id: string;
  name: string;
  message: string;
  from_number: string;
  status: string;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  created_at: string;
}

export default function SMSCampaigns() {
  const [campaigns, setCampaigns] = useState<SMSCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    message: '',
    from_number: '',
  });

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      const response = await smsAPI.list();
      setCampaigns(response.data);
    } catch (err: any) {
      setError('Failed to load SMS campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.message) {
      alert('Please fill in all required fields');
      return;
    }

    try:
      await smsAPI.create(formData);
      setShowCreateModal(false);
      setFormData({ name: '', message: '', from_number: '' });
      loadCampaigns();
    } catch (err: any) {
      alert('Failed to create SMS campaign');
    }
  };

  const handleSend = async (campaignId: string) => {
    if (!confirm('Are you sure you want to send this SMS campaign?')) return;

    try {
      await smsAPI.send(campaignId);
      alert('SMS campaign sent successfully!');
      loadCampaigns();
    } catch (err: any) {
      alert('Failed to send SMS campaign');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusStyles: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      scheduled: 'bg-blue-100 text-blue-800',
      sending: 'bg-yellow-100 text-yellow-800',
      sent: 'bg-green-100 text-green-800',
      paused: 'bg-orange-100 text-orange-800',
      cancelled: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusStyles[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">SMS Campaigns</h1>
          <p className="mt-2 text-gray-600">
            Send text messages to your leads and customers
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary"
        >
          + New SMS Campaign
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-danger-light/10 border border-danger-light rounded-lg text-danger-dark">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : campaigns.length === 0 ? (
        <div className="card text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No SMS campaigns</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating your first SMS campaign.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
            >
              + Create SMS Campaign
            </button>
          </div>
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Campaign
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Delivered
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Failed
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {campaigns.map((campaign) => (
                <tr key={campaign.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {campaign.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {campaign.message.substring(0, 50)}...
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(campaign.status)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {campaign.sent_count}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {campaign.delivered_count}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <span className={campaign.failed_count > 0 ? 'text-danger' : ''}>
                      {campaign.failed_count}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {campaign.status === 'draft' && (
                      <button
                        onClick={() => handleSend(campaign.id)}
                        className="text-primary-600 hover:text-primary-900 mr-3"
                      >
                        Send
                      </button>
                    )}
                    <button className="text-gray-600 hover:text-gray-900">
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4">
            <h2 className="text-2xl font-bold mb-6">Create SMS Campaign</h2>

            <div className="space-y-4">
              <div>
                <label className="label">Campaign Name *</label>
                <input
                  type="text"
                  className="input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Flash Sale Alert"
                />
              </div>

              <div>
                <label className="label">Message * (160 characters max)</label>
                <textarea
                  className="input"
                  rows={4}
                  maxLength={160}
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  placeholder="Your SMS message here..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.message.length}/160 characters
                </p>
              </div>

              <div>
                <label className="label">From Number (Optional)</label>
                <input
                  type="tel"
                  className="input"
                  value={formData.from_number}
                  onChange={(e) => setFormData({ ...formData, from_number: e.target.value })}
                  placeholder="+1234567890"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave blank to use default Twilio number
                </p>
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button onClick={handleCreate} className="btn btn-primary">
                Create Campaign
              </button>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setFormData({ name: '', message: '', from_number: '' });
                }}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

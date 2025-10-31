import { useState, useEffect } from 'react';
import { socialAPI } from '../services/api';

interface Post {
  id: string;
  platforms: string[];
  content: string;
  image_url?: string;
  scheduled_time?: string;
  status: string;
  created_at: string;
}

interface ConnectedAccount {
  id: string;
  platform: string;
  account_id: string;
  account_name: string;
  connected_at: string;
}

export default function SocialMedia() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    platforms: [] as string[],
    content: '',
    image_url: '',
    scheduled_time: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [postsRes, accountsRes] = await Promise.all([
        socialAPI.listPosts(),
        socialAPI.listAccounts(),
      ]);

      setPosts(postsRes.data);
      setAccounts(accountsRes.data.accounts);
    } catch (err: any) {
      setError('Failed to load data');
    } finally:
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.content || formData.platforms.length === 0) {
      alert('Please fill in content and select at least one platform');
      return;
    }

    try {
      const postData: any = {
        platforms: formData.platforms,
        content: formData.content,
      };

      if (formData.image_url) {
        postData.image_url = formData.image_url;
      }

      if (formData.scheduled_time) {
        postData.scheduled_time = new Date(formData.scheduled_time).toISOString();
      }

      await socialAPI.createPost(postData);
      setShowCreateModal(false);
      setFormData({ platforms: [], content: '', image_url: '', scheduled_time: '' });
      loadData();
    } catch (err: any) {
      alert('Failed to create post: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handlePlatformToggle = (platform: string) => {
    if (formData.platforms.includes(platform)) {
      setFormData({
        ...formData,
        platforms: formData.platforms.filter((p) => p !== platform),
      });
    } else {
      setFormData({
        ...formData,
        platforms: [...formData.platforms, platform],
      });
    }
  };

  const handlePublishNow = async (postId: string) => {
    if (!confirm('Publish this post now?')) return;

    try {
      await socialAPI.publishNow(postId);
      alert('Post published successfully!');
      loadData();
    } catch (err: any) {
      alert('Failed to publish post');
    }
  };

  const handleDisconnect = async (accountId: string) => {
    if (!confirm('Disconnect this account?')) return;

    try {
      await socialAPI.disconnectAccount(accountId);
      loadData();
    } catch (err: any) {
      alert('Failed to disconnect account');
    }
  };

  const getPlatformIcon = (platform: string) => {
    const icons: Record<string, string> = {
      facebook: '📘',
      instagram: '📷',
      twitter: '🐦',
    };
    return icons[platform] || '📱';
  };

  const getStatusBadge = (status: string) => {
    const statusStyles: Record<string, string> = {
      scheduled: 'bg-blue-100 text-blue-800',
      publishing: 'bg-yellow-100 text-yellow-800',
      published: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusStyles[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Social Media Management</h1>
        <p className="mt-2 text-gray-600">
          Manage your social media posts across platforms
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-danger-light/10 border border-danger-light rounded-lg text-danger-dark">
          {error}
        </div>
      )}

      {/* Connected Accounts */}
      <div className="card mb-6">
        <h2 className="text-xl font-semibold mb-4">Connected Accounts</h2>

        {accounts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No accounts connected yet</p>
            <p className="text-sm mt-2">
              Connect your social media accounts to start posting
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {accounts.map((account) => (
              <div key={account.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{getPlatformIcon(account.platform)}</span>
                    <div>
                      <div className="font-medium">{account.account_name}</div>
                      <div className="text-xs text-gray-500">{account.platform}</div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDisconnect(account.id)}
                    className="text-danger hover:text-danger-dark text-sm"
                  >
                    Disconnect
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Post Button */}
      <div className="mb-6">
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary"
        >
          + Create New Post
        </button>
      </div>

      {/* Posts List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : posts.length === 0 ? (
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
              d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No posts yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Create your first social media post
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {posts.map((post) => (
            <div key={post.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div className="flex gap-2">
                  {post.platforms.map((platform) => (
                    <span key={platform} className="text-2xl">
                      {getPlatformIcon(platform)}
                    </span>
                  ))}
                </div>
                {getStatusBadge(post.status)}
              </div>

              <p className="text-sm text-gray-700 mb-3">
                {post.content.substring(0, 100)}
                {post.content.length > 100 && '...'}
              </p>

              {post.image_url && (
                <div className="mb-3 h-40 bg-gray-100 rounded-lg flex items-center justify-center">
                  <img
                    src={post.image_url}
                    alt="Post"
                    className="max-h-full max-w-full object-contain rounded-lg"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
              )}

              {post.scheduled_time && (
                <p className="text-xs text-gray-500 mb-3">
                  Scheduled: {new Date(post.scheduled_time).toLocaleString()}
                </p>
              )}

              <div className="flex gap-2">
                {post.status === 'scheduled' && (
                  <button
                    onClick={() => handlePublishNow(post.id)}
                    className="text-sm btn btn-primary flex-1"
                  >
                    Publish Now
                  </button>
                )}
                <button className="text-sm btn btn-secondary flex-1">View</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Post Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full mx-4 my-8">
            <h2 className="text-2xl font-bold mb-6">Create Social Media Post</h2>

            <div className="space-y-4">
              <div>
                <label className="label">Select Platforms *</label>
                <div className="flex gap-3">
                  {['facebook', 'instagram', 'twitter'].map((platform) => (
                    <button
                      key={platform}
                      onClick={() => handlePlatformToggle(platform)}
                      className={`px-4 py-2 rounded-lg border-2 transition-colors ${
                        formData.platforms.includes(platform)
                          ? 'border-primary-600 bg-primary-50'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      {getPlatformIcon(platform)} {platform.charAt(0).toUpperCase() + platform.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="label">Content *</label>
                <textarea
                  className="input"
                  rows={6}
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="Write your post content here..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.content.length} characters
                </p>
              </div>

              <div>
                <label className="label">Image URL (Optional)</label>
                <input
                  type="url"
                  className="input"
                  value={formData.image_url}
                  onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  placeholder="https://example.com/image.jpg"
                />
              </div>

              <div>
                <label className="label">Schedule (Optional)</label>
                <input
                  type="datetime-local"
                  className="input"
                  value={formData.scheduled_time}
                  onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave blank to post immediately
                </p>
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button onClick={handleCreate} className="btn btn-primary">
                {formData.scheduled_time ? 'Schedule Post' : 'Post Now'}
              </button>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setFormData({ platforms: [], content: '', image_url: '', scheduled_time: '' });
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

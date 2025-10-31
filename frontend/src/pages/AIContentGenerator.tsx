import { useState } from 'react';
import { aiAPI } from '../services/api';

export default function AIContentGenerator() {
  const [formData, setFormData] = useState({
    content_type: 'email',
    target_audience: '',
    main_message: '',
    tone: 'professional',
    platform: 'openai',
  });

  const [generatedContent, setGeneratedContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleGenerate = async () => {
    setError('');
    setLoading(true);

    try {
      const response = await aiAPI.generateContent(formData);
      setGeneratedContent(response.data.content);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate content. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedContent);
    alert('Content copied to clipboard!');
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">AI Content Generator</h1>
        <p className="mt-2 text-gray-600">
          Generate marketing content using AI in seconds
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">Content Settings</h2>

          <div className="space-y-4">
            <div>
              <label className="label">Content Type</label>
              <select
                name="content_type"
                value={formData.content_type}
                onChange={handleChange}
                className="input"
              >
                <option value="email">Email Campaign</option>
                <option value="social">Social Media Post</option>
                <option value="blog">Blog Post</option>
                <option value="ad">Ad Copy</option>
              </select>
            </div>

            <div>
              <label className="label">Target Audience</label>
              <input
                type="text"
                name="target_audience"
                value={formData.target_audience}
                onChange={handleChange}
                className="input"
                placeholder="e.g., Small business owners, Tech enthusiasts..."
              />
            </div>

            <div>
              <label className="label">Main Message</label>
              <textarea
                name="main_message"
                value={formData.main_message}
                onChange={handleChange}
                className="input"
                rows={3}
                placeholder="What is the key message you want to convey?"
              />
            </div>

            <div>
              <label className="label">Tone & Style</label>
              <select
                name="tone"
                value={formData.tone}
                onChange={handleChange}
                className="input"
              >
                <option value="professional">Professional</option>
                <option value="friendly">Friendly</option>
                <option value="humorous">Humorous</option>
                <option value="urgent">Urgent</option>
                <option value="inspiring">Inspiring</option>
              </select>
            </div>

            <div>
              <label className="label">AI Platform</label>
              <select
                name="platform"
                value={formData.platform}
                onChange={handleChange}
                className="input"
              >
                <option value="openai">OpenAI (GPT-4)</option>
                <option value="anthropic">Anthropic (Claude)</option>
              </select>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading || !formData.target_audience || !formData.main_message}
              className="w-full btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </span>
              ) : (
                '✨ Generate with AI'
              )}
            </button>
          </div>
        </div>

        {/* Output */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">Generated Content</h2>

          {error && (
            <div className="mb-4 p-3 bg-danger-light/10 border border-danger-light rounded-lg text-danger-dark text-sm">
              {error}
            </div>
          )}

          {generatedContent ? (
            <div>
              <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200 min-h-[300px] whitespace-pre-wrap">
                {generatedContent}
              </div>

              <div className="flex gap-3">
                <button onClick={handleCopy} className="btn btn-primary">
                  📋 Copy to Clipboard
                </button>
                <button
                  onClick={handleGenerate}
                  disabled={loading}
                  className="btn btn-secondary disabled:opacity-50"
                >
                  🔄 Regenerate
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-400">
              <div className="text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <p className="mt-2 text-sm">
                  Your generated content will appear here
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

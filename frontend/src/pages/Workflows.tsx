import { useState, useEffect } from 'react';
import { workflowsAPI } from '../services/api';

interface Workflow {
  id: string;
  name: string;
  trigger_type: string;
  active: boolean;
  steps: any[];
  created_at: string;
}

export default function Workflows() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTemplates, setShowTemplates] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadWorkflows();
    loadTemplates();
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await workflowsAPI.list();
      setWorkflows(response.data);
    } catch (err: any) {
      setError('Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await workflowsAPI.getTemplates();
      setTemplates(response.data.templates);
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  };

  const toggleWorkflow = async (workflowId: string, currentState: boolean) => {
    try {
      if (currentState) {
        await workflowsAPI.deactivate(workflowId);
      } else {
        await workflowsAPI.activate(workflowId);
      }
      loadWorkflows();
    } catch (err: any) {
      alert('Failed to toggle workflow');
    }
  };

  const deleteWorkflow = async (workflowId: string) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      await workflowsAPI.delete(workflowId);
      loadWorkflows();
    } catch (err: any) {
      alert('Failed to delete workflow');
    }
  };

  const createFromTemplate = async (template: any) => {
    try {
      await workflowsAPI.create({
        name: template.name,
        trigger_type: template.trigger_type,
        steps: template.steps,
      });
      setShowTemplates(false);
      loadWorkflows();
    } catch (err: any) {
      alert('Failed to create workflow from template');
    }
  };

  const getTriggerLabel = (triggerType: string) => {
    const labels: Record<string, string> = {
      new_signup: '👤 New Signup',
      cart_abandoned: '🛒 Cart Abandoned',
      form_submit: '📝 Form Submit',
      purchase: '💳 Purchase',
      page_visit: '🌐 Page Visit',
      inactive_30_days: '😴 Inactive 30 Days',
    };
    return labels[triggerType] || triggerType;
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Automation</h1>
          <p className="mt-2 text-gray-600">
            Automate your marketing with trigger-based workflows
          </p>
        </div>
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          className="btn btn-primary"
        >
          📋 {showTemplates ? 'Hide Templates' : 'Browse Templates'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-danger-light/10 border border-danger-light rounded-lg text-danger-dark">
          {error}
        </div>
      )}

      {/* Templates Section */}
      {showTemplates && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Workflow Templates</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div key={template.id} className="card">
                <h3 className="text-lg font-semibold text-gray-900">
                  {template.name}
                </h3>
                <p className="mt-2 text-sm text-gray-600">{template.description}</p>
                <div className="mt-3 flex items-center text-sm text-gray-500">
                  <span className="mr-2">Trigger:</span>
                  <span className="font-medium">
                    {getTriggerLabel(template.trigger_type)}
                  </span>
                </div>
                <div className="mt-3 text-sm text-gray-500">
                  {template.steps.length} steps
                </div>
                <button
                  onClick={() => createFromTemplate(template)}
                  className="mt-4 w-full btn btn-primary"
                >
                  Use Template
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Workflows List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : workflows.length === 0 ? (
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
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No workflows</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a workflow from a template.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowTemplates(true)}
              className="btn btn-primary"
            >
              Browse Templates
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {workflow.name}
                  </h3>
                  <p className="mt-1 text-sm text-gray-600">
                    {getTriggerLabel(workflow.trigger_type)}
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={workflow.active}
                    onChange={() => toggleWorkflow(workflow.id, workflow.active)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="mt-4 flex items-center text-sm">
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium ${
                    workflow.active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {workflow.active ? '✓ Active' : '○ Inactive'}
                </span>
                <span className="ml-3 text-gray-500">
                  {workflow.steps.length} steps
                </span>
              </div>

              <div className="mt-4 flex gap-2">
                <button className="flex-1 btn btn-secondary text-sm">
                  Edit
                </button>
                <button
                  onClick={() => deleteWorkflow(workflow.id)}
                  className="px-4 py-2 text-sm text-danger hover:text-danger-dark"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

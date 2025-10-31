import React, { useState, useEffect } from 'react';
import { abTestAPI } from '../services/api';

interface ABTest {
  id: string;
  name: string;
  description?: string;
  type: 'email' | 'sms';
  status: 'draft' | 'running' | 'completed' | 'cancelled';
  variant_a: VariantData;
  variant_b: VariantData;
  test_percentage: number;
  variant_split: number;
  winner_metric: string;
  wait_time_hours: number;
  auto_send_winner: boolean;
  winner_variant?: string;
  winner_confidence?: number;
  variant_a_sent: number;
  variant_a_delivered: number;
  variant_a_opens: number;
  variant_a_clicks: number;
  variant_a_conversions: number;
  variant_b_sent: number;
  variant_b_delivered: number;
  variant_b_opens: number;
  variant_b_clicks: number;
  variant_b_conversions: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  winner_declared_at?: string;
}

interface VariantData {
  subject?: string;
  content: string;
  cta_text?: string;
  cta_url?: string;
  from_name?: string;
}

interface TestStats {
  variant_a: {
    sent: number;
    delivered: number;
    opens: number;
    clicks: number;
    conversions: number;
    delivery_rate: number;
    open_rate: number;
    click_rate: number;
    conversion_rate: number;
    response_rate: number;
  };
  variant_b: {
    sent: number;
    delivered: number;
    opens: number;
    clicks: number;
    conversions: number;
    delivery_rate: number;
    open_rate: number;
    click_rate: number;
    conversion_rate: number;
    response_rate: number;
  };
  winner?: string;
  confidence?: number;
  ready_to_declare: boolean;
}

export default function ABTesting() {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTest, setSelectedTest] = useState<ABTest | null>(null);
  const [stats, setStats] = useState<TestStats | null>(null);
  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'email' as 'email' | 'sms',
    variant_a: {
      subject: '',
      content: '',
      cta_text: '',
      cta_url: '',
      from_name: '',
    },
    variant_b: {
      subject: '',
      content: '',
      cta_text: '',
      cta_url: '',
      from_name: '',
    },
    test_percentage: 20,
    variant_split: 50,
    winner_metric: 'open_rate',
    wait_time_hours: 24,
    auto_send_winner: true,
  });

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    setLoading(true);
    try {
      const response = await abTestAPI.list();
      setTests(response.data);
    } catch (error) {
      console.error('Failed to load A/B tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async (testId: string) => {
    try {
      const response = await abTestAPI.getStats(testId);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.variant_a.content || !formData.variant_b.content) {
      alert('이름과 두 가지 변형의 내용을 입력해주세요');
      return;
    }

    try {
      await abTestAPI.create(formData);
      alert('A/B 테스트가 생성되었습니다!');
      setShowCreateModal(false);
      resetForm();
      loadTests();
    } catch (error) {
      console.error('Failed to create A/B test:', error);
      alert('A/B 테스트 생성에 실패했습니다');
    }
  };

  const handleCheckWinner = async (testId: string) => {
    try {
      const response = await abTestAPI.checkWinner(testId);
      if (response.data.winner_declared) {
        alert(`승자 선언: 변형 ${response.data.winner_variant} (신뢰도: ${response.data.confidence}%)`);
        loadTests();
      } else {
        alert('아직 승자를 선언할 수 없습니다. 더 많은 데이터가 필요합니다.');
      }
    } catch (error) {
      console.error('Failed to check winner:', error);
    }
  };

  const handleManualDeclare = async (testId: string, variant: string) => {
    if (!confirm(`변형 ${variant}을(를) 승자로 선언하시겠습니까?`)) {
      return;
    }

    try {
      await abTestAPI.declareWinner(testId, variant);
      alert(`변형 ${variant}이(가) 승자로 선언되었습니다`);
      loadTests();
    } catch (error) {
      console.error('Failed to declare winner:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      type: 'email',
      variant_a: {
        subject: '',
        content: '',
        cta_text: '',
        cta_url: '',
        from_name: '',
      },
      variant_b: {
        subject: '',
        content: '',
        cta_text: '',
        cta_url: '',
        from_name: '',
      },
      test_percentage: 20,
      variant_split: 50,
      winner_metric: 'open_rate',
      wait_time_hours: 24,
      auto_send_winner: true,
    });
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      draft: 'bg-gray-200 text-gray-800',
      running: 'bg-blue-200 text-blue-800',
      completed: 'bg-green-200 text-green-800',
      cancelled: 'bg-red-200 text-red-800',
    };
    return badges[status as keyof typeof badges] || badges.draft;
  };

  const calculateRate = (numerator: number, denominator: number) => {
    if (denominator === 0) return '0.0';
    return ((numerator / denominator) * 100).toFixed(1);
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">A/B 테스팅</h1>
          <p className="text-gray-600 mt-2">
            이메일과 SMS 캠페인을 최적화하여 전환율을 높이세요
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 새 A/B 테스트
        </button>
      </div>

      {/* Test List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">A/B 테스트 목록</h2>
          {loading ? (
            <p className="text-gray-500 text-center py-8">로딩 중...</p>
          ) : tests.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              아직 생성된 A/B 테스트가 없습니다
            </p>
          ) : (
            <div className="space-y-4">
              {tests.map((test) => (
                <div
                  key={test.id}
                  className="border rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                  onClick={() => {
                    setSelectedTest(test);
                    loadStats(test.id);
                  }}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-semibold text-lg">{test.name}</h3>
                      {test.description && (
                        <p className="text-gray-600 text-sm">{test.description}</p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(
                          test.status
                        )}`}
                      >
                        {test.status.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-purple-200 text-purple-800">
                        {test.type.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {test.status === 'running' && (
                    <div className="mt-4 grid grid-cols-2 gap-4">
                      <div className="bg-blue-50 p-3 rounded">
                        <div className="text-sm font-semibold text-blue-900 mb-1">
                          변형 A
                        </div>
                        <div className="text-xs text-gray-600">
                          발송: {test.variant_a_sent} | 오픈:{' '}
                          {calculateRate(test.variant_a_opens, test.variant_a_delivered)}%
                        </div>
                      </div>
                      <div className="bg-green-50 p-3 rounded">
                        <div className="text-sm font-semibold text-green-900 mb-1">
                          변형 B
                        </div>
                        <div className="text-xs text-gray-600">
                          발송: {test.variant_b_sent} | 오픈:{' '}
                          {calculateRate(test.variant_b_opens, test.variant_b_delivered)}%
                        </div>
                      </div>
                    </div>
                  )}

                  {test.winner_variant && (
                    <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded p-3">
                      <div className="text-sm font-semibold text-yellow-900">
                        🏆 승자: 변형 {test.winner_variant}
                        {test.winner_confidence && (
                          <span className="ml-2 text-xs">
                            (신뢰도: {test.winner_confidence.toFixed(1)}%)
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {test.status === 'running' && !test.winner_variant && (
                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCheckWinner(test.id);
                        }}
                        className="text-sm bg-blue-600 text-white px-4 py-1 rounded hover:bg-blue-700"
                      >
                        승자 확인
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleManualDeclare(test.id, 'A');
                        }}
                        className="text-sm bg-gray-600 text-white px-4 py-1 rounded hover:bg-gray-700"
                      >
                        A 선택
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleManualDeclare(test.id, 'B');
                        }}
                        className="text-sm bg-gray-600 text-white px-4 py-1 rounded hover:bg-gray-700"
                      >
                        B 선택
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">새 A/B 테스트 생성</h2>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-6">
                {/* Basic Info */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    테스트 이름 *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    placeholder="예: 이메일 제목 테스트"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    설명
                  </label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    placeholder="테스트에 대한 간단한 설명"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    캠페인 유형 *
                  </label>
                  <select
                    value={formData.type}
                    onChange={(e) =>
                      setFormData({ ...formData, type: e.target.value as 'email' | 'sms' })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                  >
                    <option value="email">이메일</option>
                    <option value="sms">SMS</option>
                  </select>
                </div>

                {/* Variant A */}
                <div className="border-2 border-blue-300 rounded-lg p-4 bg-blue-50">
                  <h3 className="font-semibold text-lg mb-4 text-blue-900">변형 A</h3>

                  {formData.type === 'email' && (
                    <>
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          제목 *
                        </label>
                        <input
                          type="text"
                          value={formData.variant_a.subject}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              variant_a: { ...formData.variant_a, subject: e.target.value },
                            })
                          }
                          className="w-full border border-gray-300 rounded-lg px-4 py-2"
                          placeholder="이메일 제목"
                        />
                      </div>

                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          발신자 이름
                        </label>
                        <input
                          type="text"
                          value={formData.variant_a.from_name}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              variant_a: { ...formData.variant_a, from_name: e.target.value },
                            })
                          }
                          className="w-full border border-gray-300 rounded-lg px-4 py-2"
                          placeholder="발신자 이름"
                        />
                      </div>
                    </>
                  )}

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      내용 *
                    </label>
                    <textarea
                      value={formData.variant_a.content}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          variant_a: { ...formData.variant_a, content: e.target.value },
                        })
                      }
                      className="w-full border border-gray-300 rounded-lg px-4 py-2"
                      rows={4}
                      placeholder="메시지 내용"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        CTA 버튼 텍스트
                      </label>
                      <input
                        type="text"
                        value={formData.variant_a.cta_text}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            variant_a: { ...formData.variant_a, cta_text: e.target.value },
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="지금 시작하기"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        CTA URL
                      </label>
                      <input
                        type="text"
                        value={formData.variant_a.cta_url}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            variant_a: { ...formData.variant_a, cta_url: e.target.value },
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="https://..."
                      />
                    </div>
                  </div>
                </div>

                {/* Variant B */}
                <div className="border-2 border-green-300 rounded-lg p-4 bg-green-50">
                  <h3 className="font-semibold text-lg mb-4 text-green-900">변형 B</h3>

                  {formData.type === 'email' && (
                    <>
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          제목 *
                        </label>
                        <input
                          type="text"
                          value={formData.variant_b.subject}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              variant_b: { ...formData.variant_b, subject: e.target.value },
                            })
                          }
                          className="w-full border border-gray-300 rounded-lg px-4 py-2"
                          placeholder="이메일 제목"
                        />
                      </div>

                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          발신자 이름
                        </label>
                        <input
                          type="text"
                          value={formData.variant_b.from_name}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              variant_b: { ...formData.variant_b, from_name: e.target.value },
                            })
                          }
                          className="w-full border border-gray-300 rounded-lg px-4 py-2"
                          placeholder="발신자 이름"
                        />
                      </div>
                    </>
                  )}

                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      내용 *
                    </label>
                    <textarea
                      value={formData.variant_b.content}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          variant_b: { ...formData.variant_b, content: e.target.value },
                        })
                      }
                      className="w-full border border-gray-300 rounded-lg px-4 py-2"
                      rows={4}
                      placeholder="메시지 내용"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        CTA 버튼 텍스트
                      </label>
                      <input
                        type="text"
                        value={formData.variant_b.cta_text}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            variant_b: { ...formData.variant_b, cta_text: e.target.value },
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="시작하기"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        CTA URL
                      </label>
                      <input
                        type="text"
                        value={formData.variant_b.cta_url}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            variant_b: { ...formData.variant_b, cta_url: e.target.value },
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="https://..."
                      />
                    </div>
                  </div>
                </div>

                {/* Test Settings */}
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h3 className="font-semibold text-lg mb-4">테스트 설정</h3>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        테스트 비율 ({formData.test_percentage}%)
                      </label>
                      <input
                        type="range"
                        min="5"
                        max="50"
                        value={formData.test_percentage}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            test_percentage: Number(e.target.value),
                          })
                        }
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        전체 수신자 중 테스트에 사용할 비율
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        A/B 분할 ({formData.variant_split}% / {100 - formData.variant_split}%)
                      </label>
                      <input
                        type="range"
                        min="10"
                        max="90"
                        value={formData.variant_split}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            variant_split: Number(e.target.value),
                          })
                        }
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500 mt-1">변형 A와 B의 비율</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        승자 결정 기준
                      </label>
                      <select
                        value={formData.winner_metric}
                        onChange={(e) =>
                          setFormData({ ...formData, winner_metric: e.target.value })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                      >
                        <option value="open_rate">오픈율</option>
                        <option value="click_rate">클릭율</option>
                        <option value="conversion_rate">전환율</option>
                        {formData.type === 'sms' && (
                          <option value="response_rate">응답률</option>
                        )}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        대기 시간 (시간)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="168"
                        value={formData.wait_time_hours}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            wait_time_hours: Number(e.target.value),
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        승자 선언까지 대기할 시간
                      </p>
                    </div>
                  </div>

                  <div className="mt-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.auto_send_winner}
                        onChange={(e) =>
                          setFormData({ ...formData, auto_send_winner: e.target.checked })
                        }
                        className="mr-2"
                      />
                      <span className="text-sm text-gray-700">
                        승자 자동 발송 (나머지 수신자에게 자동으로 발송)
                      </span>
                    </label>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    onClick={() => {
                      setShowCreateModal(false);
                      resetForm();
                    }}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    취소
                  </button>
                  <button
                    onClick={handleCreate}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    생성
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

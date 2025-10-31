import React, { useState, useEffect } from 'react';
import { segmentAPI } from '../services/api';

interface Segment {
  id: string;
  name: string;
  description?: string;
  segment_type: 'static' | 'dynamic';
  filter_logic: 'and' | 'or';
  filters: FilterCondition[];
  lead_count: number;
  auto_update: boolean;
  created_at: string;
  last_calculated_at?: string;
}

interface FilterCondition {
  field_type: string;
  field_name?: string;
  operator: string;
  value: any;
}

const FIELD_TYPES = [
  { value: 'lead_property', label: '리드 속성' },
  { value: 'lead_score', label: '리드 점수' },
  { value: 'lead_status', label: '리드 상태' },
  { value: 'lead_source', label: '리드 소스' },
  { value: 'lead_tag', label: '태그' },
  { value: 'last_activity_date', label: '마지막 활동일' },
];

const PROPERTY_FIELDS = [
  { value: 'email', label: '이메일' },
  { value: 'name', label: '이름' },
  { value: 'company', label: '회사명' },
  { value: 'title', label: '직함' },
  { value: 'phone', label: '전화번호' },
];

const OPERATORS = {
  text: [
    { value: 'equals', label: '같음' },
    { value: 'not_equals', label: '같지 않음' },
    { value: 'contains', label: '포함함' },
    { value: 'not_contains', label: '포함하지 않음' },
    { value: 'starts_with', label: '시작함' },
    { value: 'ends_with', label: '끝남' },
    { value: 'is_empty', label: '비어있음' },
    { value: 'is_not_empty', label: '비어있지 않음' },
  ],
  number: [
    { value: 'equals', label: '같음' },
    { value: 'not_equals', label: '같지 않음' },
    { value: 'greater_than', label: '보다 큼' },
    { value: 'less_than', label: '보다 작음' },
    { value: 'greater_than_or_equal', label: '이상' },
    { value: 'less_than_or_equal', label: '이하' },
  ],
  date: [
    { value: 'in_last_days', label: '최근 N일 이내' },
    { value: 'greater_than', label: '이후' },
    { value: 'less_than', label: '이전' },
  ],
};

export default function Segments() {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<Segment | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [previewCount, setPreviewCount] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    segment_type: 'dynamic' as 'dynamic' | 'static',
    filter_logic: 'and' as 'and' | 'or',
    filters: [] as FilterCondition[],
    auto_update: true,
  });

  useEffect(() => {
    loadSegments();
  }, []);

  const loadSegments = async () => {
    setLoading(true);
    try {
      const response = await segmentAPI.list();
      setSegments(response.data);
    } catch (error) {
      console.error('Failed to load segments:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSegment = async (id: string) => {
    try {
      const response = await segmentAPI.get(id);
      setSelectedSegment(response.data);
    } catch (error) {
      console.error('Failed to load segment:', error);
    }
  };

  const handleCreateSegment = async () => {
    if (!formData.name) {
      alert('세그먼트 이름을 입력해주세요');
      return;
    }

    if (formData.segment_type === 'dynamic' && formData.filters.length === 0) {
      alert('최소 하나의 필터를 추가해주세요');
      return;
    }

    try {
      await segmentAPI.create(formData);
      alert('세그먼트가 생성되었습니다!');
      setShowCreateModal(false);
      resetForm();
      loadSegments();
    } catch (error) {
      console.error('Failed to create segment:', error);
      alert('세그먼트 생성에 실패했습니다');
    }
  };

  const handlePreview = async () => {
    if (formData.filters.length === 0) {
      alert('최소 하나의 필터를 추가해주세요');
      return;
    }

    try {
      const response = await segmentAPI.preview({
        filter_logic: formData.filter_logic,
        filters: formData.filters,
      });
      setPreviewCount(response.data.count);
    } catch (error) {
      console.error('Failed to preview segment:', error);
      alert('프리뷰 실패');
    }
  };

  const handleRecalculate = async (segmentId: string) => {
    try {
      await segmentAPI.calculate(segmentId);
      alert('세그먼트가 재계산되었습니다!');
      loadSegments();
      if (selectedSegment?.id === segmentId) {
        loadSegment(segmentId);
      }
    } catch (error) {
      console.error('Failed to recalculate segment:', error);
      alert('재계산 실패');
    }
  };

  const handleDeleteSegment = async (segmentId: string) => {
    if (!confirm('이 세그먼트를 삭제하시겠습니까?')) return;

    try {
      await segmentAPI.delete(segmentId);
      alert('세그먼트가 삭제되었습니다');
      loadSegments();
      if (selectedSegment?.id === segmentId) {
        setSelectedSegment(null);
      }
    } catch (error) {
      console.error('Failed to delete segment:', error);
      alert('삭제 실패');
    }
  };

  const addFilter = () => {
    setFormData({
      ...formData,
      filters: [
        ...formData.filters,
        {
          field_type: 'lead_property',
          field_name: 'email',
          operator: 'contains',
          value: '',
        },
      ],
    });
    setPreviewCount(null);
  };

  const updateFilter = (index: number, updates: Partial<FilterCondition>) => {
    const newFilters = [...formData.filters];
    newFilters[index] = { ...newFilters[index], ...updates };
    setFormData({ ...formData, filters: newFilters });
    setPreviewCount(null);
  };

  const removeFilter = (index: number) => {
    const newFilters = formData.filters.filter((_, i) => i !== index);
    setFormData({ ...formData, filters: newFilters });
    setPreviewCount(null);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      segment_type: 'dynamic',
      filter_logic: 'and',
      filters: [],
      auto_update: true,
    });
    setPreviewCount(null);
  };

  const getStatusBadge = (segment: Segment) => {
    return segment.segment_type === 'static'
      ? 'bg-purple-200 text-purple-800'
      : 'bg-blue-200 text-blue-800';
  };

  const getOperatorLabel = (operator: string) => {
    const allOperators = [...OPERATORS.text, ...OPERATORS.number, ...OPERATORS.date];
    return allOperators.find((op) => op.value === operator)?.label || operator;
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">세그먼트</h1>
          <p className="text-gray-600 mt-2">
            정확한 타겟팅을 위한 오디언스 세그먼트를 만드세요
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 새 세그먼트
        </button>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Segment List */}
        <div className="col-span-4">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-lg">세그먼트 목록</h2>
            </div>
            <div className="divide-y max-h-[calc(100vh-250px)] overflow-y-auto">
              {loading ? (
                <p className="p-4 text-gray-500 text-center">로딩 중...</p>
              ) : segments.length === 0 ? (
                <p className="p-4 text-gray-500 text-center">
                  아직 생성된 세그먼트가 없습니다
                </p>
              ) : (
                segments.map((segment) => (
                  <div
                    key={segment.id}
                    onClick={() => {
                      setSelectedSegment(segment);
                      loadSegment(segment.id);
                    }}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedSegment?.id === segment.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">{segment.name}</h3>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusBadge(
                          segment
                        )}`}
                      >
                        {segment.segment_type === 'static' ? '정적' : '동적'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      {segment.description || '설명 없음'}
                    </p>
                    <div className="flex justify-between items-center text-xs text-gray-500">
                      <span>👥 {segment.lead_count} 리드</span>
                      <span>{segment.filters.length} 필터</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Segment Detail */}
        <div className="col-span-8">
          {!selectedSegment ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500">세그먼트를 선택하거나 새로 만들어보세요</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Header */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-2xl font-bold mb-2">{selectedSegment.name}</h2>
                    <p className="text-gray-600">{selectedSegment.description}</p>
                    <div className="flex gap-4 mt-3 text-sm">
                      <span
                        className={`px-3 py-1 rounded-full font-semibold ${getStatusBadge(
                          selectedSegment
                        )}`}
                      >
                        {selectedSegment.segment_type === 'static' ? '정적 세그먼트' : '동적 세그먼트'}
                      </span>
                      <span className="text-gray-500">
                        로직: {selectedSegment.filter_logic.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {selectedSegment.segment_type === 'dynamic' && (
                      <button
                        onClick={() => handleRecalculate(selectedSegment.id)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                      >
                        재계산
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteSegment(selectedSegment.id)}
                      className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
                    >
                      삭제
                    </button>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {selectedSegment.lead_count}
                    </div>
                    <div className="text-xs text-gray-500">총 리드</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {selectedSegment.filters.length}
                    </div>
                    <div className="text-xs text-gray-500">필터 조건</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-600">
                      {selectedSegment.last_calculated_at
                        ? new Date(selectedSegment.last_calculated_at).toLocaleString('ko-KR')
                        : '계산 안됨'}
                    </div>
                    <div className="text-xs text-gray-500">마지막 계산</div>
                  </div>
                </div>
              </div>

              {/* Filters */}
              {selectedSegment.segment_type === 'dynamic' && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-xl font-semibold mb-4">필터 조건</h3>
                  {selectedSegment.filters.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">필터가 없습니다</p>
                  ) : (
                    <div className="space-y-3">
                      {selectedSegment.filters.map((filter, index) => (
                        <div
                          key={index}
                          className="border border-gray-200 rounded-lg p-4 bg-gray-50"
                        >
                          <div className="grid grid-cols-4 gap-3 text-sm">
                            <div>
                              <div className="font-semibold text-gray-700">필드</div>
                              <div className="text-gray-600">
                                {filter.field_name || filter.field_type}
                              </div>
                            </div>
                            <div>
                              <div className="font-semibold text-gray-700">연산자</div>
                              <div className="text-gray-600">
                                {getOperatorLabel(filter.operator)}
                              </div>
                            </div>
                            <div className="col-span-2">
                              <div className="font-semibold text-gray-700">값</div>
                              <div className="text-gray-600 truncate">
                                {typeof filter.value === 'boolean'
                                  ? filter.value
                                    ? '예'
                                    : '아니오'
                                  : filter.value}
                              </div>
                            </div>
                          </div>
                          {index < selectedSegment.filters.length - 1 && (
                            <div className="text-center mt-2 text-xs font-semibold text-blue-600">
                              {selectedSegment.filter_logic.toUpperCase()}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create Segment Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">새 세그먼트 생성</h2>
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

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    세그먼트 이름 *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    placeholder="예: 고가치 리드"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    설명
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    rows={2}
                    placeholder="세그먼트에 대한 설명"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    세그먼트 유형
                  </label>
                  <select
                    value={formData.segment_type}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        segment_type: e.target.value as 'dynamic' | 'static',
                      })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                  >
                    <option value="dynamic">동적 (필터 기반 자동 업데이트)</option>
                    <option value="static">정적 (수동으로 리드 추가)</option>
                  </select>
                </div>

                {formData.segment_type === 'dynamic' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        필터 로직
                      </label>
                      <select
                        value={formData.filter_logic}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            filter_logic: e.target.value as 'and' | 'or',
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                      >
                        <option value="and">AND (모든 조건 충족)</option>
                        <option value="or">OR (하나라도 충족)</option>
                      </select>
                    </div>

                    {/* Filter Builder */}
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <label className="block text-sm font-medium text-gray-700">
                          필터 조건
                        </label>
                        <button
                          onClick={addFilter}
                          className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                        >
                          + 필터 추가
                        </button>
                      </div>

                      {formData.filters.length === 0 ? (
                        <p className="text-gray-500 text-sm text-center py-4 border border-dashed rounded">
                          필터를 추가하여 세그먼트 조건을 설정하세요
                        </p>
                      ) : (
                        <div className="space-y-3">
                          {formData.filters.map((filter, index) => (
                            <div key={index} className="border rounded-lg p-4 bg-gray-50">
                              <div className="grid grid-cols-12 gap-3 mb-2">
                                <div className="col-span-3">
                                  <select
                                    value={filter.field_type}
                                    onChange={(e) =>
                                      updateFilter(index, { field_type: e.target.value })
                                    }
                                    className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                                  >
                                    {FIELD_TYPES.map((ft) => (
                                      <option key={ft.value} value={ft.value}>
                                        {ft.label}
                                      </option>
                                    ))}
                                  </select>
                                </div>

                                {filter.field_type === 'lead_property' && (
                                  <div className="col-span-3">
                                    <select
                                      value={filter.field_name || ''}
                                      onChange={(e) =>
                                        updateFilter(index, { field_name: e.target.value })
                                      }
                                      className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                                    >
                                      {PROPERTY_FIELDS.map((pf) => (
                                        <option key={pf.value} value={pf.value}>
                                          {pf.label}
                                        </option>
                                      ))}
                                    </select>
                                  </div>
                                )}

                                <div className="col-span-3">
                                  <select
                                    value={filter.operator}
                                    onChange={(e) =>
                                      updateFilter(index, { operator: e.target.value })
                                    }
                                    className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                                  >
                                    {OPERATORS.text.map((op) => (
                                      <option key={op.value} value={op.value}>
                                        {op.label}
                                      </option>
                                    ))}
                                  </select>
                                </div>

                                <div className="col-span-2">
                                  <input
                                    type="text"
                                    value={filter.value}
                                    onChange={(e) =>
                                      updateFilter(index, { value: e.target.value })
                                    }
                                    className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                                    placeholder="값"
                                  />
                                </div>

                                <div className="col-span-1 flex justify-end">
                                  <button
                                    onClick={() => removeFilter(index)}
                                    className="text-red-600 hover:text-red-800"
                                  >
                                    ✕
                                  </button>
                                </div>
                              </div>

                              {index < formData.filters.length - 1 && (
                                <div className="text-center text-xs font-semibold text-blue-600 mt-2">
                                  {formData.filter_logic.toUpperCase()}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Preview */}
                    {formData.filters.length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex justify-between items-center">
                          <div>
                            <div className="font-semibold text-blue-900">
                              {previewCount !== null ? (
                                <>매칭되는 리드: {previewCount}개</>
                              ) : (
                                '프리뷰를 확인하세요'
                              )}
                            </div>
                            <p className="text-xs text-blue-700 mt-1">
                              현재 필터 조건으로 매칭되는 리드 수를 미리 확인할 수 있습니다
                            </p>
                          </div>
                          <button
                            onClick={handlePreview}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
                          >
                            프리뷰
                          </button>
                        </div>
                      </div>
                    )}

                    <div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.auto_update}
                          onChange={(e) =>
                            setFormData({ ...formData, auto_update: e.target.checked })
                          }
                          className="mr-2"
                        />
                        <span className="text-sm text-gray-700">
                          자동 업데이트 (새 리드가 조건에 맞으면 자동 추가)
                        </span>
                      </label>
                    </div>
                  </>
                )}

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
                    onClick={handleCreateSegment}
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

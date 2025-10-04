<template>
  <div class="course-analytics">
    <header
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
    >
      <Breadcrumbs class="h-7" :items="breadcrumbs" />
    </header>

    <div class="p-5">
      <div v-if="loading" class="flex justify-center py-10">
        <div class="spinner"></div>
      </div>

      <template v-else>
        <div class="course-header mb-6">
          <h1 class="text-2xl font-bold">{{ courseData.title }}</h1>
          <div class="mt-2 flex flex-wrap gap-4">
            <div class="filter-group">
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Date Range') }}</label>
              <div class="date-range flex items-center gap-2">
                <input 
                  type="date" 
                  v-model="filters.fromDate" 
                  class="rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
                <span>{{ __('to') }}</span>
                <input 
                  type="date" 
                  v-model="filters.toDate" 
                  class="rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            
            <div class="filter-group ml-auto flex items-end gap-2">
              <Button 
                appearance="primary" 
                @click="applyFilters"
              >
                {{ __('Apply Filters') }}
              </Button>
              <Button 
                appearance="secondary" 
                @click="exportCSV"
              >
                {{ __('Export CSV') }}
              </Button>
            </div>
          </div>
        </div>

        <div class="dashboard-cards grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ formatTime(analytics.summary.total_active_time) }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Total Time Spent') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ analytics.summary.total_students }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Active Students') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ formatTime(analytics.summary.avg_time_per_student) }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Avg. Time per Student') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-sm text-gray-600">{{ __('Completion Status') }}</div>
                <div class="mt-1 flex items-center gap-2">
                  <span class="inline-block h-3 w-3 rounded-full bg-green-500"></span>
                  <span class="text-sm">{{ __('Complete') }}: {{ analytics.summary.completion_stats.Complete }}</span>
                </div>
                <div class="mt-1 flex items-center gap-2">
                  <span class="inline-block h-3 w-3 rounded-full bg-yellow-500"></span>
                  <span class="text-sm">{{ __('Partial') }}: {{ analytics.summary.completion_stats['Partially Complete'] }}</span>
                </div>
                <div class="mt-1 flex items-center gap-2">
                  <span class="inline-block h-3 w-3 rounded-full bg-red-500"></span>
                  <span class="text-sm">{{ __('Incomplete') }}: {{ analytics.summary.completion_stats.Incomplete }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div class="chart-container rounded-lg border bg-white p-4 shadow-sm">
            <h2 class="mb-4 text-lg font-medium">{{ __('Time Spent by Chapter/Lesson') }}</h2>
            <div class="h-64">
              <AxisChart
                v-if="unitChartData.length"
                :config="{
                  data: unitChartData,
                  title: '',
                  xAxis: {
                    key: 'name',
                    type: 'category',
                    title: 'Unit',
                  },
                  yAxis: {
                    title: 'Minutes',
                  },
                  series: [
                    { name: 'time_spent', type: 'bar', valueFormatter: (v) => `${Math.round(v)}m` }
                  ],
                }"
              />
              <div v-else class="flex h-full items-center justify-center">
                <p class="text-gray-500">{{ __('No data available') }}</p>
              </div>
            </div>
          </div>

          <div class="chart-container rounded-lg border bg-white p-4 shadow-sm">
            <h2 class="mb-4 text-lg font-medium">{{ __('Daily Activity') }}</h2>
            <div class="h-64">
              <AxisChart
                v-if="dailyChartData.length"
                :config="{
                  data: dailyChartData,
                  title: '',
                  xAxis: {
                    key: 'date',
                    type: 'time',
                    title: 'Date',
                    timeGrain: 'day',
                  },
                  yAxis: {
                    title: 'Minutes',
                  },
                  series: [
                    { name: 'time_spent', type: 'line', showDataPoints: true, valueFormatter: (v) => `${Math.round(v)}m` }
                  ],
                }"
              />
              <div v-else class="flex h-full items-center justify-center">
                <p class="text-gray-500">{{ __('No data available') }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6">
          <h2 class="mb-4 text-lg font-medium">{{ __('Unit Details') }}</h2>
          <div class="overflow-x-auto rounded-lg border bg-white shadow-sm">
            <table class="w-full table-auto">
              <thead class="bg-gray-50 text-left text-sm font-medium text-gray-500">
                <tr>
                  <th class="px-4 py-3">{{ __('Chapter/Lesson') }}</th>
                  <th class="px-4 py-3">{{ __('Time Spent') }}</th>
                  <th class="px-4 py-3">{{ __('Sessions') }}</th>
                  <th class="px-4 py-3">{{ __('Students') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y text-sm text-gray-700">
                <tr v-for="(unit, index) in analytics.units" :key="index" class="hover:bg-gray-50">
                  <td class="px-4 py-3">
                    <div class="font-medium">{{ unit.chapter_name || unit.lesson_name }}</div>
                    <div v-if="unit.chapter_name && unit.lesson_name" class="text-xs text-gray-500">
                      {{ unit.lesson_name }}
                    </div>
                  </td>
                  <td class="px-4 py-3">{{ formatTime(unit.total_active_time) }}</td>
                  <td class="px-4 py-3">{{ unit.total_sessions }}</td>
                  <td class="px-4 py-3">{{ unit.unique_students }}</td>
                </tr>
                <tr v-if="!analytics.units.length">
                  <td colspan="4" class="px-4 py-8 text-center text-gray-500">
                    {{ __('No data available') }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="mt-6">
          <h2 class="mb-4 text-lg font-medium">{{ __('Student Details') }}</h2>
          <div class="overflow-x-auto rounded-lg border bg-white shadow-sm">
            <table class="w-full table-auto">
              <thead class="bg-gray-50 text-left text-sm font-medium text-gray-500">
                <tr>
                  <th class="px-4 py-3">{{ __('Student') }}</th>
                  <th class="px-4 py-3">{{ __('Time Spent') }}</th>
                  <th class="px-4 py-3">{{ __('Sessions') }}</th>
                  <th class="px-4 py-3">{{ __('Days Active') }}</th>
                  <th class="px-4 py-3">{{ __('Actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y text-sm text-gray-700">
                <tr v-for="(student, index) in analytics.students" :key="index" class="hover:bg-gray-50">
                  <td class="px-4 py-3">{{ student.member_name }}</td>
                  <td class="px-4 py-3">{{ formatTime(student.total_active_time) }}</td>
                  <td class="px-4 py-3">{{ student.total_sessions }}</td>
                  <td class="px-4 py-3">{{ student.days_active }}</td>
                  <td class="px-4 py-3">
                    <Button 
                      appearance="minimal" 
                      @click="viewStudentDetails(student.member)"
                      class="text-sm"
                    >
                      {{ __('View Details') }}
                    </Button>
                  </td>
                </tr>
                <tr v-if="!analytics.students.length">
                  <td colspan="5" class="px-4 py-8 text-center text-gray-500">
                    {{ __('No data available') }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import {
  AxisChart,
  Breadcrumbs,
  Button,
  createResource,
  usePageMeta,
} from 'frappe-ui'
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { sessionStore } from '../stores/session'

const router = useRouter()
const route = useRoute()
const { brand } = sessionStore()

// Course data
const courseId = route.params.course
const courseData = ref({ title: '' })
const loading = ref(true)

// Filters
const filters = ref({
  fromDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  toDate: new Date().toISOString().split('T')[0]
})

// Analytics data
const analytics = ref({
  summary: {
    total_active_time: 0,
    total_students: 0,
    avg_time_per_student: 0,
    completion_stats: {
      Complete: 0,
      'Partially Complete': 0,
      Incomplete: 0
    }
  },
  units: [],
  students: [],
  daily: []
})

// Breadcrumbs
const breadcrumbs = computed(() => {
  return [
    {
      label: 'Analytics Dashboard',
      route: {
        name: 'AdminAnalytics',
      },
    },
    {
      label: courseData.value.title || 'Course Analytics',
      route: {
        name: 'CourseAnalytics',
        params: { course: courseId }
      },
    }
  ]
})

// Chart data
const unitChartData = computed(() => {
  return analytics.value.units.map(unit => ({
    name: unit.chapter_name || unit.lesson_name,
    time_spent: unit.total_active_time / 60 // Convert to minutes
  })).slice(0, 15) // Limit to 15 items for readability
})

const dailyChartData = computed(() => {
  return analytics.value.daily.map(day => ({
    date: new Date(day.date),
    time_spent: day.total_active_time / 60 // Convert to minutes
  }))
})

// Resources
const courseResource = createResource({
  url: 'lms.lms.api.get_course',
  params: { course_name: courseId },
  auto: true,
  onSuccess: (data) => {
    courseData.value = data || {}
  }
})

const analyticsResource = createResource({
  url: 'lms.lms.learning_analytics_api.get_course_analytics',
  onSuccess: (data) => {
    analytics.value = data || analytics.value
    loading.value = false
  },
  onError: () => {
    loading.value = false
  }
})

// Methods
function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m`
}

function applyFilters() {
  loading.value = true
  analyticsResource.submit({
    course: courseId,
    from_date: filters.value.fromDate,
    to_date: filters.value.toDate
  })
}

function exportCSV() {
  const params = new URLSearchParams({
    course: courseId,
    from_date: filters.value.fromDate,
    to_date: filters.value.toDate
  })
  
  window.open(`/api/method/lms.lms.learning_analytics_api.export_analytics_csv?${params.toString()}`, '_blank')
}

function viewStudentDetails(student) {
  router.push({ 
    name: 'StudentAnalytics', 
    params: { student } 
  })
}

// Load initial data
onMounted(() => {
  applyFilters()
})

// Page meta
usePageMeta(() => {
  return {
    title: __('Course Analytics'),
    icon: brand.favicon,
  }
})
</script>

<style scoped>
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>

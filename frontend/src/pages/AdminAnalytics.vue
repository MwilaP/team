<template>
  <div class="analytics-dashboard">
    <header
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
    >
      <Breadcrumbs class="h-7" :items="breadcrumbs" />
    </header>

    <div class="p-5">
      <div class="filters mb-6 flex flex-wrap gap-4 border-b pb-4">
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
        
        <div class="filter-group">
          <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Course') }}</label>
          <select 
            v-model="filters.course" 
            class="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">{{ __('All Courses') }}</option>
            <option v-for="course in courses" :key="course.name" :value="course.name">
              {{ course.title }}
            </option>
          </select>
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
      
      <div v-if="loading" class="flex justify-center py-10">
        <div class="spinner"></div>
      </div>

      <template v-else>
        <div class="dashboard-cards grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ formatTime(summaryStats.totalTime) }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Total Time Spent') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ summaryStats.activeStudents }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Active Students') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ summaryStats.avgCompletionRate }}%</div>
            <div class="card-label text-sm text-gray-600">{{ __('Avg. Completion Rate') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ formatTime(summaryStats.avgTimePerStudent) }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Avg. Time per Student') }}</div>
          </div>
        </div>
        
        <div class="chart-container mt-6 rounded-lg border bg-white p-4 shadow-sm">
          <h2 class="mb-4 text-lg font-medium">{{ __('Time Spent by Course') }}</h2>
          <div class="h-64">
            <AxisChart
              v-if="courseChartData.length"
              :config="{
                data: courseChartData,
                title: '',
                xAxis: {
                  key: 'course_name',
                  type: 'category',
                  title: 'Course',
                },
                yAxis: {
                  title: 'Hours',
                },
                series: [
                  { name: 'time_spent', type: 'bar', valueFormatter: (v) => formatTime(v * 3600) }
                ],
              }"
            />
            <div v-else class="flex h-full items-center justify-center">
              <p class="text-gray-500">{{ __('No data available') }}</p>
            </div>
          </div>
        </div>
        
        <div class="data-tables mt-6">
          <h2 class="mb-4 text-lg font-medium">{{ __('Student Time Analytics') }}</h2>
          <div class="overflow-x-auto rounded-lg border bg-white shadow-sm">
            <table class="w-full table-auto">
              <thead class="bg-gray-50 text-left text-sm font-medium text-gray-500">
                <tr>
                  <th class="px-4 py-3">{{ __('Student') }}</th>
                  <th class="px-4 py-3">{{ __('Course') }}</th>
                  <th class="px-4 py-3">{{ __('Time Spent') }}</th>
                  <th class="px-4 py-3">{{ __('Completion') }}</th>
                  <th class="px-4 py-3">{{ __('Last Active') }}</th>
                  <th class="px-4 py-3">{{ __('Actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y text-sm text-gray-700">
                <tr v-for="(row, index) in analyticsData" :key="index" class="hover:bg-gray-50">
                  <td class="px-4 py-3">{{ row.member_name }}</td>
                  <td class="px-4 py-3">{{ row.course_name }}</td>
                  <td class="px-4 py-3">{{ formatTime(row.total_active_time) }}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center">
                      <div class="h-2 w-full max-w-[100px] rounded-full bg-gray-200">
                        <div 
                          class="h-full rounded-full bg-green-500" 
                          :style="{ width: `${row.completion}%` }"
                        ></div>
                      </div>
                      <span class="ml-2">{{ row.completion }}%</span>
                    </div>
                  </td>
                  <td class="px-4 py-3">{{ formatDate(row.last_active) }}</td>
                  <td class="px-4 py-3">
                    <Button 
                      appearance="minimal" 
                      @click="viewStudentDetails(row.member)"
                      class="text-sm"
                    >
                      {{ __('View Details') }}
                    </Button>
                  </td>
                </tr>
                <tr v-if="!analyticsData.length">
                  <td colspan="6" class="px-4 py-8 text-center text-gray-500">
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
import { useRouter } from 'vue-router'
import { sessionStore } from '../stores/session'

const router = useRouter()
const { brand } = sessionStore()

// Breadcrumbs
const breadcrumbs = computed(() => {
  return [
    {
      label: 'Analytics Dashboard',
      route: {
        name: 'AdminAnalytics',
      },
    },
  ]
})

// Filters
const filters = ref({
  fromDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  toDate: new Date().toISOString().split('T')[0],
  course: ''
})

// Data
const loading = ref(true)
const courses = ref([])
const analyticsData = ref([])
const summaryStats = ref({
  totalTime: 0,
  activeStudents: 0,
  avgCompletionRate: 0,
  avgTimePerStudent: 0
})

// Chart data
const courseChartData = computed(() => {
  // Group by course
  const courseData = {}
  analyticsData.value.forEach(row => {
    if (!courseData[row.course_name]) {
      courseData[row.course_name] = 0
    }
    courseData[row.course_name] += row.total_active_time
  })
  
  // Convert to chart format
  return Object.entries(courseData).map(([course_name, total_active_time]) => ({
    course_name,
    time_spent: total_active_time / 3600 // Convert to hours
  }))
})

// Resources
const coursesResource = createResource({
  url: 'lms.lms.api.get_courses',
  auto: true,
  onSuccess: (data) => {
    courses.value = data || []
  }
})

const analyticsResource = createResource({
  url: 'lms.lms.learning_analytics_api.get_admin_analytics',
  onSuccess: (data) => {
    analyticsData.value = data.data || []
    summaryStats.value = data.summary || summaryStats.value
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

function formatDate(dateString) {
  if (!dateString) return 'Never'
  return new Date(dateString).toLocaleDateString()
}

function applyFilters() {
  loading.value = true
  analyticsResource.submit({
    from_date: filters.value.fromDate,
    to_date: filters.value.toDate,
    course: filters.value.course
  })
}

function exportCSV() {
  const params = new URLSearchParams({
    from_date: filters.value.fromDate,
    to_date: filters.value.toDate,
    course: filters.value.course
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
    title: __('Analytics Dashboard'),
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

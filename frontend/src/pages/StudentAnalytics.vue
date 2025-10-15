<template>
  <div class="student-analytics">
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
        <div class="student-header mb-6">
          <div class="flex items-center gap-4">
            <UserAvatar :user="studentId" size="lg" />
            <div>
              <h1 class="text-2xl font-bold">{{ studentName }}</h1>
              <p class="text-gray-600">{{ studentId }}</p>
            </div>
          </div>
          
          <div class="mt-4 flex flex-wrap gap-4">
            <div class="filter-group" v-if="courses.length > 1">
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Course') }}</label>
              <select 
                v-model="selectedCourseIndex" 
                class="rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option v-for="(course, index) in courses" :key="index" :value="index">
                  {{ course.course.title }}
                </option>
              </select>
            </div>
            
            <div class="filter-group ml-auto flex items-end gap-2">
              <Button 
                appearance="secondary" 
                @click="exportCSV"
              >
                {{ __('Export CSV') }}
              </Button>
            </div>
          </div>
        </div>

        <div v-if="selectedCourse">
          <div class="dashboard-cards grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div class="card rounded-lg border bg-white p-4 shadow-sm">
              <div class="card-value text-2xl font-bold">{{ formatTime(selectedCourse.summary.total_active_time) }}</div>
              <div class="card-label text-sm text-gray-600">{{ __('Total Time Spent') }}</div>
            </div>
            
            <div class="card rounded-lg border bg-white p-4 shadow-sm">
              <div class="card-value text-2xl font-bold">{{ selectedCourse.summary.sessions_count }}</div>
              <div class="card-label text-sm text-gray-600">{{ __('Total Sessions') }}</div>
            </div>
            
            <div class="card rounded-lg border bg-white p-4 shadow-sm">
              <div class="card-value text-2xl font-bold">{{ selectedCourse.summary.days_active }}</div>
              <div class="card-label text-sm text-gray-600">{{ __('Days Active') }}</div>
            </div>
            
            <div class="card rounded-lg border bg-white p-4 shadow-sm">
              <div class="flex flex-col">
                <div class="card-label text-sm text-gray-600">{{ __('Course Completion') }}</div>
                <div class="mt-2 flex items-center gap-2">
                  <div class="h-2 w-full max-w-[150px] rounded-full bg-gray-200">
                    <div 
                      class="h-full rounded-full bg-green-500" 
                      :style="{ width: `${selectedCourse.summary.completion}%` }"
                    ></div>
                  </div>
                  <span>{{ selectedCourse.summary.completion }}%</span>
                </div>
                <div class="mt-2 text-sm text-gray-600">
                  {{ __('First access') }}: {{ formatDate(selectedCourse.summary.first_access) }}
                </div>
                <div class="text-sm text-gray-600">
                  {{ __('Last access') }}: {{ formatDate(selectedCourse.summary.last_access) }}
                </div>
              </div>
            </div>
          </div>

          <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div class="chart-container rounded-lg border bg-white p-4 shadow-sm">
              <h2 class="mb-4 text-lg font-medium">{{ __('Time Spent by Chapter') }}</h2>
              <div class="h-64">
                <AxisChart
                  v-if="chapterChartData.length"
                  :config="{
                    data: chapterChartData,
                    title: '',
                    xAxis: {
                      key: 'title',
                      type: 'category',
                      title: 'Chapter',
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
            <h2 class="mb-4 text-lg font-medium">{{ __('Chapter & Lesson Details') }}</h2>
            <div class="overflow-x-auto rounded-lg border bg-white shadow-sm">
              <table class="w-full table-auto">
                <thead class="bg-gray-50 text-left text-sm font-medium text-gray-500">
                  <tr>
                    <th class="px-4 py-3">{{ __('Chapter/Lesson') }}</th>
                    <th class="px-4 py-3">{{ __('Time Spent') }}</th>
                    <th class="px-4 py-3">{{ __('Last Access') }}</th>
                  </tr>
                </thead>    
                <tbody>
                  <template v-for="(chapter, chapterIndex) in selectedCourse.chapters" :key="chapterIndex">
                    <!-- Chapter row -->
                    <tr class="bg-gray-50 font-medium">
                      <td class="px-4 py-3">{{ chapter.title }}</td>
                      <td class="px-4 py-3">{{ formatTime(chapter.total_active_time) }}</td>
                      <td class="px-4 py-3">-</td>
                    </tr>
                    
                    <!-- Lesson rows -->
                    <tr 
                      v-for="(lesson, lessonIndex) in chapter.lessons" 
                      :key="`${chapterIndex}-${lessonIndex}`"
                      class="hover:bg-gray-50"
                    >
                      <td class="pl-8 py-3 pr-4 text-sm">{{ lesson.title }}</td>
                      <td class="px-4 py-3 text-sm">{{ formatTime(lesson.active_time) }}</td>
                      <td class="px-4 py-3 text-sm">{{ formatDate(lesson.last_access) }}</td>
                    </tr>
                    
                    <!-- Empty state for no lessons -->
                    <tr v-if="!chapter.lessons.length">
                      <td colspan="3" class="pl-8 py-3 pr-4 text-sm text-gray-500">
                        {{ __('No lesson data available') }}
                      </td>
                    </tr>
                  </template>
                  
                  <!-- Empty state for no chapters -->
                  <tr v-if="!selectedCourse.chapters.length">
                    <td colspan="3" class="px-4 py-8 text-center text-gray-500">
                      {{ __('No chapter data available') }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <!-- Empty state for no courses -->
        <div v-else class="mt-10 text-center">
          <p class="text-gray-500">{{ __('No course data available for this student') }}</p>
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
import { computed, ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { sessionStore } from '../stores/session'
import UserAvatar from '../components/UserAvatar.vue'

const router = useRouter()
const route = useRoute()
const { brand } = sessionStore()

// Student data
const studentId = route.params.student
const studentName = ref('')
const loading = ref(true)
const courses = ref([])
const selectedCourseIndex = ref(0)

// Computed
const selectedCourse = computed(() => {
  return courses.value[selectedCourseIndex.value] || null
})

const chapterChartData = computed(() => {
  if (!selectedCourse.value) return []
  
  return selectedCourse.value.chapters.map(chapter => ({
    title: chapter.title,
    time_spent: chapter.total_active_time / 60 // Convert to minutes
  }))
})

const dailyChartData = computed(() => {
  if (!selectedCourse.value) return []
  
  return selectedCourse.value.daily_activity.map(day => ({
    date: new Date(day.date),
    time_spent: day.active_time / 60 // Convert to minutes
  }))
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
      label: studentName.value || studentId,
      route: {
        name: 'StudentAnalytics',
        params: { student: studentId }
      },
    }
  ]
})

// Resources
const userResource = createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'User',
    filters: { name: studentId },
    fieldname: 'full_name'
  },
  auto: true,
  onSuccess: (data) => {
    if (data && data.message) {
      studentName.value = data.message.full_name || studentId
    }
  }
})

const analyticsResource = createResource({
  url: 'lms.lms.learning_analytics_api.get_student_analytics',
  onSuccess: (data) => {
    courses.value = data || []
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

function exportCSV() {
  const params = new URLSearchParams({
    student: studentId,
    course: selectedCourse.value?.course?.name || ''
  })
  
  window.open(`/api/method/lms.lms.learning_analytics_api.export_analytics_csv?${params.toString()}`, '_blank')
}

// Load initial data
onMounted(() => {
  analyticsResource.submit({
    student: studentId
  })
})

// Page meta
usePageMeta(() => {
  return {
    title: __('Student Analytics'),
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

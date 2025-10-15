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
            <div class="card-value text-2xl font-bold">{{ summaryStats.totalStudents }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Total Students') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ summaryStats.activeStudents }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Active Students') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ formatTime(summaryStats.totalTime) }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Total Time Spent') }}</div>
          </div>
          
          <div class="card rounded-lg border bg-white p-4 shadow-sm">
            <div class="card-value text-2xl font-bold">{{ formatTime(summaryStats.avgTimePerStudent) }}</div>
            <div class="card-label text-sm text-gray-600">{{ __('Avg. Time per Student') }}</div>
          </div>
        </div>
        
        <div class="students-section mt-6">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-lg font-medium">{{ __('Students on Platform') }}</h2>
            <div class="search-box">
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="Search students..."
                class="rounded-md border border-gray-300 px-3 py-2 text-sm"
                @input="filterStudents"
              />
            </div>
          </div>
          
          <div class="overflow-x-auto rounded-lg border bg-white shadow-sm">
            <table class="w-full table-auto">
              <thead class="bg-gray-50 text-left text-sm font-medium text-gray-500">
                <tr>
                  <th class="px-4 py-3">{{ __('Student') }}</th>
                  <th class="px-4 py-3">{{ __('Email') }}</th>
                  <th class="px-4 py-3">{{ __('Courses Enrolled') }}</th>
                  <th class="px-4 py-3">{{ __('Time Spent') }}</th>
                  <th class="px-4 py-3">{{ __('Last Active') }}</th>
                  <th class="px-4 py-3">{{ __('Status') }}</th>
                  <th class="px-4 py-3">{{ __('Actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y text-sm text-gray-700">
                <tr v-for="student in filteredStudents" :key="student.member" class="hover:bg-gray-50">
                  <td class="px-4 py-3">
                    <div class="flex items-center space-x-3">
                      <div class="student-avatar flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600 font-medium text-xs">
                        {{ getInitials(student.member_name) }}
                      </div>
                      <span class="font-medium">{{ student.member_name }}</span>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-gray-600">{{ student.email }}</td>
                  <td class="px-4 py-3">{{ student.courses_count }}</td>
                  <td class="px-4 py-3">{{ formatTime(student.total_time) }}</td>
                  <td class="px-4 py-3">{{ formatDate(student.last_active) }}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center">
                      <div 
                        class="h-2 w-2 rounded-full mr-2"
                        :class="student.is_active ? 'bg-green-500' : 'bg-gray-400'"
                      ></div>
                      <span class="text-xs">
                        {{ student.is_active ? __('Active') : __('Inactive') }}
                      </span>
                    </div>
                  </td>
                  <td class="px-4 py-3">
                    <button 
                      @click="viewStudentDetails(student.member)"
                      class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      {{ __('View Analytics') }}
                    </button>
                  </td>
                </tr>
                <tr v-if="!filteredStudents.length">
                  <td colspan="7" class="px-4 py-8 text-center text-gray-500">
                    {{ searchQuery ? __('No students found matching your search') : __('No students found') }}
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
      label: 'Students Dashboard',
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
const studentsData = ref([])
const searchQuery = ref('')
const summaryStats = ref({
  totalStudents: 0,
  activeStudents: 0,
  totalTime: 0,
  avgTimePerStudent: 0
})

// Filtered students based on search
const filteredStudents = computed(() => {
  if (!searchQuery.value) {
    return studentsData.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return studentsData.value.filter(student => 
    student.member_name.toLowerCase().includes(query) ||
    student.email.toLowerCase().includes(query)
  )
})

// Resources
const coursesResource = createResource({
  url: 'lms.lms.api.get_courses',
  auto: true,
  onSuccess: (data) => {
    courses.value = data || []
  }
})

// Resource to get all enrolled students
const enrolledStudentsResource = createResource({
  url: 'frappe.client.get_list',
  makeParams: () => ({
    doctype: 'LMS Enrollment',
    fields: ['member', 'course', 'progress', 'creation'],
    filters: {},
    limit_page_length: 0
  }),
  auto: false,
  onError: (error) => {
    console.error('Enrollments resource error:', error)
  }
})

// Resource to get analytics data
const analyticsResource = createResource({
  url: 'lms.lms.learning_analytics_api.get_admin_analytics',
  auto: false,
  onError: (error) => {
    console.error('Analytics resource error:', error)
  }
})

// Resource to get user details
const usersResource = createResource({
  url: 'lms.lms.api.get_members',
  makeParams: () => ({
    start: 0,
    search: ''
  }),
  auto: false
})

const studentsResource = createResource({
  url: 'lms.lms.api.get_members',
  makeParams: () => ({
    start: 0,
    search: ''
  }),
  onSuccess: async (allUsers) => {
    console.log('Got users:', allUsers?.length || 0)
    try {
      // Get enrollments data
      const enrollmentsResponse = await enrolledStudentsResource.submit()
      const enrollments = enrollmentsResponse || []
      
      // Get analytics data
      const analyticsResponse = await analyticsResource.submit({
        from_date: filters.value.fromDate,
        to_date: filters.value.toDate,
        course: filters.value.course
      })
      const analyticsData = analyticsResponse?.data || []
      
      // Create analytics map for quick lookup
      const analyticsMap = new Map()
      analyticsData.forEach(item => {
        const key = item.member
        if (!analyticsMap.has(key)) {
          analyticsMap.set(key, {
            total_time: 0,
            courses: new Set(),
            completions: [],
            last_active: null
          })
        }
        
        const analytics = analyticsMap.get(key)
        analytics.total_time += item.total_active_time || 0
        analytics.courses.add(item.course)
        analytics.completions.push(item.completion || 0)
        
        if (item.last_active) {
          if (!analytics.last_active || new Date(item.last_active) > new Date(analytics.last_active)) {
            analytics.last_active = item.last_active
          }
        }
      })
      
      // Create enrollments map for course counts
      const enrollmentsMap = new Map()
      enrollments.forEach(enrollment => {
        if (!enrollmentsMap.has(enrollment.member)) {
          enrollmentsMap.set(enrollment.member, {
            courses: new Set(),
            enrollments: []
          })
        }
        enrollmentsMap.get(enrollment.member).courses.add(enrollment.course)
        enrollmentsMap.get(enrollment.member).enrollments.push(enrollment)
      })
      
      // Filter users to only include those with enrollments (students)
      const enrolledUserEmails = new Set(enrollments.map(e => e.member))
      const enrolledUsers = allUsers.filter(user => enrolledUserEmails.has(user.name))
      
      // Process all enrolled students
      const processedStudents = enrolledUsers.map(user => {
        const analytics = analyticsMap.get(user.name)
        const enrollmentData = enrollmentsMap.get(user.name)
        
        const student = {
          member: user.name,
          member_name: user.full_name || user.name,
          email: user.name,
          total_time: analytics?.total_time || 0,
          courses_count: enrollmentData?.courses.size || 0,
          avg_completion: 0,
          last_active: analytics?.last_active || user.last_active,
          is_active: false
        }
        
        // Calculate average completion
        if (analytics?.completions.length > 0) {
          student.avg_completion = Math.round(
            analytics.completions.reduce((a, b) => a + b, 0) / analytics.completions.length
          )
        } else if (enrollmentData?.enrollments.length > 0) {
          const progressValues = enrollmentData.enrollments
            .map(e => parseFloat(e.progress) || 0)
            .filter(p => p > 0)
          if (progressValues.length > 0) {
            student.avg_completion = Math.round(
              progressValues.reduce((a, b) => a + b, 0) / progressValues.length
            )
          }
        }
        
        // Determine if active (last activity within 7 days)
        if (student.last_active) {
          const daysSinceActive = (new Date() - new Date(student.last_active)) / (1000 * 60 * 60 * 24)
          student.is_active = daysSinceActive <= 7
        }
        
        return student
      })
      
      studentsData.value = processedStudents
      
      // Update summary stats
      summaryStats.value = {
        totalStudents: processedStudents.length,
        activeStudents: processedStudents.filter(s => s.is_active).length,
        totalTime: analyticsResponse?.summary?.totalTime || 0,
        avgTimePerStudent: analyticsResponse?.summary?.avgTimePerStudent || 0
      }
      
      loading.value = false
    } catch (error) {
      console.error('Error loading student data:', error)
      loading.value = false
    }
  },
  onError: (error) => {
    console.error('Students resource error:', error)
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

function getInitials(name) {
  if (!name) return 'U'
  return name.split(' ')
    .map(word => word.charAt(0))
    .join('')
    .toUpperCase()
    .substring(0, 2)
}

function filterStudents() {
  // This is handled by the computed property filteredStudents
}

function applyFilters() {
  loading.value = true
  studentsResource.submit()
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
    title: __('Students Dashboard'),
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

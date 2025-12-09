import { useState, useEffect } from 'react';
import { 
  Users, ShoppingCart, DollarSign, Clock,
  TrendingUp, TrendingDown, ArrowRight
} from 'lucide-react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { StatCardSkeleton } from '@/components/common/LoadingState';
import { 
  getDashboardStats, getOrdersByStatus, 
  getRevenueByCategory, getOrdersOverTime 
} from '@/lib/api';
import { DashboardStats } from '@/lib/types';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

const COLORS = [
  'hsl(217, 91%, 50%)',
  'hsl(142, 76%, 36%)',
  'hsl(38, 92%, 50%)',
  'hsl(280, 68%, 60%)',
];

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
  loading?: boolean;
}

function StatCard({ title, value, icon, trend, loading }: StatCardProps) {
  if (loading) return <StatCardSkeleton />;

  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-semibold text-foreground">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
        </div>
        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
          {icon}
        </div>
      </div>
      {trend !== undefined && (
        <div className={cn(
          "flex items-center gap-1 mt-3 text-sm",
          trend >= 0 ? "text-success" : "text-destructive"
        )}>
          {trend >= 0 ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span>{Math.abs(trend)}% from last month</span>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [ordersByStatus, setOrdersByStatus] = useState<{ name: string; value: number }[]>([]);
  const [revenueByCategory, setRevenueByCategory] = useState<{ name: string; value: number }[]>([]);
  const [ordersOverTime, setOrdersOverTime] = useState<{ name: string; orders: number; revenue: number }[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      getDashboardStats(),
      getOrdersByStatus(),
      getRevenueByCategory(),
      getOrdersOverTime(),
    ]).then(([statsData, statusData, categoryData, timeData]) => {
      setStats(statsData);
      setOrdersByStatus(statusData);
      setRevenueByCategory(categoryData);
      setOrdersOverTime(timeData);
      setIsLoading(false);
    });
  }, []);

  return (
    <AppLayout>
      <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
            <p className="text-muted-foreground">
              Key metrics and insights at a glance
            </p>
          </div>
          <Button onClick={() => navigate('/')}>
            <ArrowRight className="w-4 h-4" />
            New Query
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Customers"
            value={stats?.totalCustomers ?? 0}
            icon={<Users className="w-5 h-5" />}
            trend={stats?.customerGrowth}
            loading={isLoading}
          />
          <StatCard
            title="Total Orders"
            value={stats?.totalOrders ?? 0}
            icon={<ShoppingCart className="w-5 h-5" />}
            trend={stats?.orderGrowth}
            loading={isLoading}
          />
          <StatCard
            title="Total Revenue"
            value={stats ? `$${stats.totalRevenue.toLocaleString()}` : '$0'}
            icon={<DollarSign className="w-5 h-5" />}
            trend={stats?.revenueGrowth}
            loading={isLoading}
          />
          <StatCard
            title="Pending Orders"
            value={stats?.pendingOrders ?? 0}
            icon={<Clock className="w-5 h-5" />}
            loading={isLoading}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Orders Over Time */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
            <h3 className="font-medium text-foreground mb-4">Orders Over Time</h3>
            <div className="h-[280px]">
              {isLoading ? (
                <div className="h-full bg-muted rounded animate-pulse" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={ordersOverTime} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))', 
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="orders" stroke={COLORS[0]} strokeWidth={2} />
                    <Line type="monotone" dataKey="revenue" stroke={COLORS[1]} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Orders by Status */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft">
            <h3 className="font-medium text-foreground mb-4">Orders by Status</h3>
            <div className="h-[280px]">
              {isLoading ? (
                <div className="h-full bg-muted rounded animate-pulse" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ordersByStatus} layout="vertical" margin={{ top: 10, right: 30, left: 80, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={true} vertical={false} />
                    <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis type="category" dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))', 
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {ordersByStatus.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Revenue by Category */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-soft lg:col-span-2">
            <h3 className="font-medium text-foreground mb-4">Revenue by Category</h3>
            <div className="h-[280px]">
              {isLoading ? (
                <div className="h-full bg-muted rounded animate-pulse" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={revenueByCategory} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))', 
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                      }}
                      formatter={(value: number) => [`$${value.toLocaleString()}`, 'Revenue']}
                    />
                    <Bar dataKey="value" fill={COLORS[0]} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

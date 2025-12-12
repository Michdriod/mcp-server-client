import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Calendar,
  Clock,
  FileText,
  Mail,
  Play,
  Trash2,
  Edit,
  Plus,
  CheckCircle,
  XCircle,
  Pause,
} from 'lucide-react';
import {
  listScheduledReports,
  createScheduledReport,
  updateScheduledReport,
  deleteScheduledReport,
  executeScheduledReport,
  getSavedQueries,
  ScheduledReport,
} from '@/lib/api';
import { SavedQuery } from '@/lib/types';
import { toast } from '@/hooks/use-toast';
import { AppLayout } from '@/components/layout/AppLayout';

// Cron expression presets
const CRON_PRESETS = [
  { label: 'Every day at 9:00 AM', value: '0 9 * * *' },
  { label: 'Every Monday at 9:00 AM', value: '0 9 * * 1' },
  { label: 'Every weekday at 9:00 AM', value: '0 9 * * 1-5' },
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every 6 hours', value: '0 */6 * * *' },
  { label: 'First day of month at 9:00 AM', value: '0 9 1 * *' },
  { label: 'Custom', value: 'custom' },
];

export default function ScheduledReportsPage() {
  const [reports, setReports] = useState<ScheduledReport[]>([]);
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingReport, setEditingReport] = useState<ScheduledReport | null>(null);
  const [deletingReportId, setDeletingReportId] = useState<number | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    saved_query_id: 0,
    schedule_cron: '0 9 * * *',
    cronPreset: '0 9 * * *',
    format: 'csv' as 'csv' | 'excel' | 'pdf',
    recipients: '',
    is_active: true,
  });

  // Custom cron state
  const [customCron, setCustomCron] = useState({
    hour: '9',
    minute: '0',
    frequency: 'daily',
    selectedDays: [] as number[],
    dayOfMonth: '1'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [reportsData, queriesData] = await Promise.all([
        listScheduledReports(),
        getSavedQueries(),
      ]);
      setReports(reportsData);
      setSavedQueries(queriesData);
    } catch (error) {
      toast({
        title: 'Failed to Load Data',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Helper functions for custom cron
  const updateCustomCron = (field: string, value: string) => {
    setCustomCron(prev => {
      const newCron = { ...prev, [field]: value };
      
      // Update the cron expression when any field changes
      const cronExpression = generateCronExpression(newCron);
      setFormData(prevForm => ({ ...prevForm, schedule_cron: cronExpression }));
      
      return newCron;
    });
  };

  const toggleDay = (dayIndex: number) => {
    setCustomCron(prev => {
      const selectedDays = prev.selectedDays.includes(dayIndex)
        ? prev.selectedDays.filter(d => d !== dayIndex)
        : [...prev.selectedDays, dayIndex].sort();
      
      const newCron = { ...prev, selectedDays };
      const cronExpression = generateCronExpression(newCron);
      setFormData(prevForm => ({ ...prevForm, schedule_cron: cronExpression }));
      
      return newCron;
    });
  };

  const generateCronExpression = (cron: typeof customCron) => {
    const minute = cron.minute || '0';
    const hour = cron.hour || '9';
    
    switch (cron.frequency) {
      case 'daily':
        return `${minute} ${hour} * * *`;
      case 'weekly':
        const dayOfWeek = cron.selectedDays.length > 0 ? cron.selectedDays.join(',') : '1';
        return `${minute} ${hour} * * ${dayOfWeek}`;
      case 'monthly':
        const day = cron.dayOfMonth || '1';
        return `${minute} ${hour} ${day} * *`;
      case 'weekdays':
        return `${minute} ${hour} * * 1-5`;
      case 'weekends':
        return `${minute} ${hour} * * 0,6`;
      case 'custom-days':
        const customDays = cron.selectedDays.length > 0 ? cron.selectedDays.join(',') : '*';
        return `${minute} ${hour} * * ${customDays}`;
      default:
        return `${minute} ${hour} * * *`;
    }
  };

  const handleCreateOrUpdate = async () => {
    try {
      // Validate
      if (!formData.name.trim()) {
        toast({ title: 'Name is required', variant: 'destructive' });
        return;
      }
      if (!formData.saved_query_id) {
        toast({ title: 'Please select a query', variant: 'destructive' });
        return;
      }
      if (!formData.recipients.trim()) {
        toast({ title: 'At least one recipient is required', variant: 'destructive' });
        return;
      }

      const recipients = formData.recipients
        .split(',')
        .map((email) => email.trim())
        .filter((email) => email);

      if (editingReport) {
        // Update
        await updateScheduledReport(editingReport.id, {
          name: formData.name,
          description: formData.description,
          schedule_cron: formData.schedule_cron,
          format: formData.format,
          recipients,
          is_active: formData.is_active,
        });
        toast({ title: 'Report Updated', description: 'Scheduled report updated successfully' });
      } else {
        // Create
        await createScheduledReport({
          name: formData.name,
          description: formData.description,
          saved_query_id: formData.saved_query_id,
          schedule_cron: formData.schedule_cron,
          format: formData.format,
          recipients,
        });
        toast({ title: 'Report Created', description: 'Scheduled report created successfully' });
      }

      setShowDialog(false);
      resetForm();
      loadData();
    } catch (error) {
      toast({
        title: 'Failed to Save Report',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async () => {
    if (!deletingReportId) return;

    try {
      await deleteScheduledReport(deletingReportId);
      toast({ title: 'Report Deleted', description: 'Scheduled report deleted successfully' });
      setShowDeleteDialog(false);
      setDeletingReportId(null);
      loadData();
    } catch (error) {
      toast({
        title: 'Failed to Delete Report',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleExecuteNow = async (reportId: number, reportName: string) => {
    try {
      await executeScheduledReport(reportId);
      toast({
        title: 'Report Executed',
        description: `"${reportName}" executed successfully`,
      });
      loadData();
    } catch (error) {
      toast({
        title: 'Execution Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const handleToggleActive = async (report: ScheduledReport) => {
    try {
      await updateScheduledReport(report.id, {
        is_active: !report.isActive,
      });
      toast({
        title: report.isActive ? 'Report Paused' : 'Report Activated',
        description: `"${report.name}" is now ${report.isActive ? 'paused' : 'active'}`,
      });
      loadData();
    } catch (error) {
      toast({
        title: 'Failed to Update Status',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  const openCreateDialog = () => {
    resetForm();
    setEditingReport(null);
    setShowDialog(true);
  };

  const openEditDialog = (report: ScheduledReport) => {
    const cronPresetValue = CRON_PRESETS.find((p) => p.value === report.scheduleCron)?.value || 'custom';
    
    setFormData({
      name: report.name || '',
      description: report.description || '',
      saved_query_id: report.savedQueryId || 0,
      schedule_cron: report.scheduleCron || '0 9 * * *',
      cronPreset: cronPresetValue,
      format: report.format || 'csv',
      recipients: Array.isArray(report.recipients) ? report.recipients.join(', ') : '',
      is_active: report.isActive ?? true,
    });

    // Reset custom cron state to match the current schedule
    if (cronPresetValue === 'custom') {
      const cronParts = (report.scheduleCron || '0 9 * * *').split(' ');
      setCustomCron({
        minute: cronParts[0] || '0',
        hour: cronParts[1] || '9',
        frequency: 'daily', // Will be updated by parsing logic
        selectedDays: [],
        dayOfMonth: cronParts[2] !== '*' ? cronParts[2] : '1'
      });
    }
    
    setEditingReport(report);
    setShowDialog(true);
  };

  const openDeleteDialog = (reportId: number) => {
    setDeletingReportId(reportId);
    setShowDeleteDialog(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      saved_query_id: 0,
      schedule_cron: '0 9 * * *',
      cronPreset: '0 9 * * *',
      format: 'csv',
      recipients: '',
      is_active: true,
    });
    setEditingReport(null);
  };

  const handleCronPresetChange = (value: string) => {
    setFormData((prev) => ({
      ...prev,
      cronPreset: value,
      schedule_cron: value !== 'custom' ? value : prev.schedule_cron,
    }));
  };

  const formatNextRun = (isoString?: string) => {
    if (!isoString) return 'Not scheduled';
    const date = new Date(isoString);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (days > 0) return `in ${days} day${days > 1 ? 's' : ''}`;
    if (hours > 0) return `in ${hours} hour${hours > 1 ? 's' : ''}`;
    return 'soon';
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Scheduled Reports</h1>
          <p className="text-muted-foreground">
            Automate query execution and email delivery on a schedule
          </p>
        </div>
        <Button onClick={openCreateDialog} className="gap-2">
          <Plus className="h-4 w-4" />
          Create Report
        </Button>
      </div>

      {/* Reports List */}
      {reports.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Calendar className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Scheduled Reports</h3>
            <p className="text-muted-foreground text-center mb-4">
              Create your first scheduled report to automate query execution
            </p>
            <Button onClick={openCreateDialog} className="gap-2">
              <Plus className="h-4 w-4" />
              Create Report
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {reports.map((report) => (
            <Card key={report.id} className={!report.isActive ? 'opacity-60' : ''}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="truncate">{report.name}</CardTitle>
                    <CardDescription className="mt-1 line-clamp-2">
                      {report.description}
                    </CardDescription>
                  </div>
                  <Badge variant={report.isActive ? 'default' : 'secondary'} className="ml-2 flex-shrink-0">
                    {report.isActive ? (
                      <><CheckCircle className="h-3 w-3 mr-1" /> Active</>
                    ) : (
                      <><Pause className="h-3 w-3 mr-1" /> Paused</>
                    )}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <span className="text-muted-foreground">Next run:</span>
                    <span className="font-medium">{formatNextRun(report.nextRunAt)}</span>
                  </div>

                  <div className="flex items-center gap-2 text-sm">
                    <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <span className="text-muted-foreground">Format:</span>
                    <Badge variant="outline" className="text-xs uppercase">
                      {report.format}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-2 text-sm">
                    <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <span className="text-muted-foreground">Recipients:</span>
                    <span className="font-medium">{report.recipients.length}</span>
                  </div>

                  <div className="flex items-center gap-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExecuteNow(report.id, report.name)}
                      className="gap-1 flex-1"
                    >
                      <Play className="h-3 w-3" />
                      Run Now
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleActive(report)}
                      className="gap-1 flex-1"
                    >
                      {report.isActive ? (
                        <><Pause className="h-3 w-3" /> Pause</>
                      ) : (
                        <><Play className="h-3 w-3" /> Activate</>
                      )}
                    </Button>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openEditDialog(report)}
                      className="gap-1 flex-1"
                    >
                      <Edit className="h-3 w-3" />
                      Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openDeleteDialog(report.id)}
                      className="gap-1 flex-1 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                      Delete
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingReport ? 'Edit Report' : 'Create Scheduled Report'}</DialogTitle>
            <DialogDescription>
              Configure a report to run automatically on a schedule
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Report Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="Daily Sales Report"
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                placeholder="Daily summary of sales metrics"
                rows={2}
              />
            </div>

            <div>
              <Label htmlFor="query">Query *</Label>
              <Select
                value={formData.saved_query_id.toString()}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, saved_query_id: parseInt(value) }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a saved query" />
                </SelectTrigger>
                <SelectContent>
                  {savedQueries.map((query) => (
                    <SelectItem key={query.id} value={query.id}>
                      {query.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="cronPreset">Schedule *</Label>
              <Select value={formData.cronPreset} onValueChange={handleCronPresetChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CRON_PRESETS.map((preset) => (
                    <SelectItem key={preset.value} value={preset.value}>
                      {preset.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {formData.cronPreset === 'custom' && (
              <div className="space-y-4 p-4 border rounded-lg bg-slate-50">
                <Label className="text-sm font-medium">Custom Schedule *</Label>
                
                {/* Time Selection */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="hour" className="text-xs">Hour (0-23)</Label>
                    <Input
                      id="hour"
                      type="number"
                      min="0"
                      max="23"
                      value={customCron.hour}
                      onChange={(e) => updateCustomCron('hour', e.target.value)}
                      placeholder="9"
                    />
                  </div>
                  <div>
                    <Label htmlFor="minute" className="text-xs">Minute (0-59)</Label>
                    <Input
                      id="minute"
                      type="number"
                      min="0"
                      max="59"
                      value={customCron.minute}
                      onChange={(e) => updateCustomCron('minute', e.target.value)}
                      placeholder="0"
                    />
                  </div>
                </div>

                {/* Frequency Selection */}
                <div>
                  <Label className="text-xs">Frequency</Label>
                  <Select value={customCron.frequency} onValueChange={(value) => updateCustomCron('frequency', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select frequency" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                      <SelectItem value="monthly">Monthly</SelectItem>
                      <SelectItem value="weekdays">Weekdays (Mon-Fri)</SelectItem>
                      <SelectItem value="weekends">Weekends (Sat-Sun)</SelectItem>
                      <SelectItem value="custom-days">Custom Days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Day of Week Selection */}
                {(customCron.frequency === 'weekly' || customCron.frequency === 'custom-days') && (
                  <div>
                    <Label className="text-xs">Day of Week</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, index) => (
                        <Button
                          key={day}
                          type="button"
                          variant={customCron.selectedDays.includes(index) ? "default" : "outline"}
                          size="sm"
                          onClick={() => toggleDay(index)}
                          className="text-xs"
                        >
                          {day}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Day of Month Selection */}
                {customCron.frequency === 'monthly' && (
                  <div>
                    <Label htmlFor="dayOfMonth" className="text-xs">Day of Month (1-31)</Label>
                    <Input
                      id="dayOfMonth"
                      type="number"
                      min="1"
                      max="31"
                      value={customCron.dayOfMonth}
                      onChange={(e) => updateCustomCron('dayOfMonth', e.target.value)}
                      placeholder="1"
                    />
                  </div>
                )}

                {/* Generated Cron Expression Display */}
                <div className="bg-white p-2 rounded border">
                  <Label className="text-xs text-muted-foreground">Generated Cron Expression:</Label>
                  <p className="font-mono text-sm mt-1">{formData.schedule_cron}</p>
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="format">Format *</Label>
              <Select
                value={formData.format}
                onValueChange={(value: 'csv' | 'excel' | 'pdf') =>
                  setFormData((prev) => ({ ...prev, format: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV</SelectItem>
                  <SelectItem value="excel">Excel (.xlsx)</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="recipients">Email Recipients * (comma-separated)</Label>
              <Input
                id="recipients"
                value={formData.recipients}
                onChange={(e) => setFormData((prev) => ({ ...prev, recipients: e.target.value }))}
                placeholder="manager@example.com, team@example.com"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateOrUpdate}>
              {editingReport ? 'Update Report' : 'Create Report'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Scheduled Report?</DialogTitle>
            <DialogDescription>
              This action cannot be undone. The report will stop running and all configuration
              will be deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete Report
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </AppLayout>
  );
}

"""
Performance Monitoring Service

Implements comprehensive telemetry collection, dashboards, and alerting
for the Expert Council Betting System.

Features:
- Real-time telemetry collection for all services
- Performance metrics tracking (latency, throughput, errors)
- Dashboard data aggregation for visualization
- Alert system for performance regressions
- Service health monitoring and SLA tracking

Requirements: 3.3 - Performance monitoring and alerting
"""

import logging
import time
import json
import uuid
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics we collect"""
    COUNTER = "counter"           # Incrementing values (requests, errors)
    GAUGE = "gauge"              # Point-in-time values (memory, connections)
    HISTOGRAM = "histogram"       # Distribution of values (latency, response times)
    TIMER = "timer"              # Duration measurements
    RATE = "rate"                # Events per time unit

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: datetime
    value: Union[float, int]
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'tags': self.tags
        }

@dataclass
class Metric:
    """Metric definition and data"""
    name: str
    metric_type: MetricType
    description: str
    unit: str = ""
    service: str = ""

    # Data storage
    points: deque = field(default_factory=lambda: deque(maxlen=1000))

    # Aggregated values
    current_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def add_point(self, value: Union[float, int], tags: Dict[str, str] = None):
        """Add a new data point"""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=float(value),
            tags=tags or {}
        )

        self.points.append(point)
        self.current_value = float(value)
        self.last_updated = datetime.utcnow()

        # Update aggregated values
        self._update_aggregates()

    def _update_aggregates(self):
        """Update min, max, avg from recent points"""
        if not self.points:
            return

        values = [p.value for p in self.points]
        self.min_value = min(values)
        self.max_value = max(values)
        self.avg_value = statistics.mean(values)

@dataclass
class Alert:
    """Performance alert"""
    alert_id: str
    metric_name: str
    service: str
    severity: AlertSeverity
    message: str
    threshold_value: float
    current_value: float

    # Timing
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    # Status
    is_active: bool = True
    acknowledgment: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'metric_name': self.metric_name,
            'service': self.service,
            'severity': self.severity.value,
            'message': self.message,
            'threshold_value': self.threshold_value,
            'current_value': self.current_value,
            'triggered_at': self.triggered_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_active': self.is_active,
            'acknowledgment': self.acknowledgment,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }

@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    metric_name: str
    service: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: AlertSeverity
    message_template: str

    # Configuration
    evaluation_window_minutes: int = 5
    min_data_points: int = 3
    cooldown_minutes: int = 15

    # State
    last_triggered: Optional[datetime] = None
    is_enabled: bool = True

    def should_trigger(self, current_value: float, data_points: int) -> bool:
        """Check if alert should trigger"""
        if not self.is_enabled:
            return False

        if data_points < self.min_data_points:
            return False

        # Check cooldown
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(minutes=self.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False

        # Evaluate condition
        if self.condition == "gt":
            return current_value > self.threshold
        elif self.condition == "lt":
            return current_value < self.threshold
        elif self.condition == "gte":
            return current_value >= self.threshold
        elif self.condition == "lte":
            return current_value <= self.threshold
        elif self.condition == "eq":
            return abs(current_value - self.threshold) < 0.001

        return False

@dataclass
class ServiceHealth:
    """Service health status"""
    service_name: str
    status: ServiceStatus
    last_check: datetime

    # Health metrics
    uptime_percentage: float = 100.0
    error_rate: float = 0.0
    avg_response_time_ms: float = 0.0

    # Checks
    health_checks: Dict[str, bool] = field(default_factory=dict)

    # Issues
    current_issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'service_name': self.service_name,
            'status': self.status.value,
            'last_check': self.last_check.isoformat(),
            'uptime_percentage': self.uptime_percentage,
            'error_rate': self.error_rate,
            'avg_response_time_ms': self.avg_response_time_ms,
            'health_checks': self.health_checks,
            'current_issues': self.current_issues
        }
class PerformanceMonitoringService:
    """
    Comprehensive performance monitoring service

    Provides telemetry collection, dashboard data, anng
    for all Expert Council Betting System services
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()

        # Metrics storage
        self.metrics: Dict[str, Metric] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.service_health: Dict[str, ServiceHealth] = {}

        # Threading
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Background tasks
        self.monitoring_active = True
        self.background_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.background_thread.start()

        # Performance targets from requirements
        self.performance_targets = {
            'vector_retrieval_p95_ms': 100,
            'end_to_end_p95_ms': 6000,
            'council_projection_p95_ms': 150,
            'schema_pass_rate': 0.985,
            'critic_repair_loops_avg': 1.2
        }

        # Initialize default metrics and alert rules
        self._initialize_default_metrics()
        self._initialize_default_alert_rules()

        logger.info("PerformanceMonitoringService initialized")

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'retention_hours': 24,
            'aggregation_interval_seconds': 60,
            'alert_evaluation_interval_seconds': 30,
            'dashboard_refresh_interval_seconds': 10,
            'max_metrics_per_service': 100,
            'max_alerts_per_service': 50,
            'enable_background_monitoring': True,
            'enable_alerting': True,
            'alert_channels': ['log', 'webhook'],  # Could extend to email, slack, etc.
            'webhook_url': None
        }

    def _initialize_default_metrics(self):
        """Initialize default metrics for all services"""

        # Vector retrieval metrics
        self.register_metric(
            "vector_retrieval_latency_ms",
            MetricType.HISTOGRAM,
            "Vector retrieval latency in milliseconds",
            unit="ms",
            service="memory_retrieval"
        )

        self.register_metric(
            "vector_retrieval_success_rate",
            MetricType.GAUGE,
            "Vector retrieval success rate",
            unit="percentage",
            service="memory_retrieval"
        )

        # Schema validation metrics
        self.register_metric(
            "schema_validation_pass_rate",
            MetricType.GAUGE,
            "Schema validation pass rate",
            unit="percentage",
            service="expert_prediction"
        )

        self.register_metric(
            "schema_validation_failures",
            MetricType.COUNTER,
            "Schema validation failures count",
            service="expert_prediction"
        )

        # Expert prediction metrics
        self.register_metric(
            "expert_prediction_latency_ms",
            MetricType.HISTOGRAM,
            "Expert prediction generation latency",
            unit="ms",
            service="expert_prediction"
        )

        self.register_metric(
            "critic_repair_loops",
            MetricType.HISTOGRAM,
            "Number of critic/repair loops per prediction",
            service="expert_prediction"
        )

        # Council selection metrics
        self.register_metric(
            "council_selection_latency_ms",
            MetricType.HISTOGRAM,
            "Council selection latency",
            unit="ms",
            service="council_selection"
        )

        self.register_metric(
            "coherence_projection_latency_ms",
            MetricType.HISTOGRAM,
            "Coherence projection latency",
            unit="ms",
            service="coherence_projection"
        )

        # Settlement metrics
        self.register_metric(
            "settlement_processing_time_ms",
            MetricType.HISTOGRAM,
            "Settlement processing time",
            unit="ms",
            service="settlement"
        )

        self.register_metric(
            "grading_accuracy",
            MetricType.GAUGE,
            "Grading accuracy percentage",
            unit="percentage",
            service="grading"
        )

        # Neo4j provenance metrics
        self.register_metric(
            "neo4j_write_latency_ms",
            MetricType.HISTOGRAM,
            "Neo4j write operation latency",
            unit="ms",
            service="neo4j_provenance"
        )

        self.register_metric(
            "neo4j_merge_conflicts",
            MetricType.COUNTER,
            "Neo4j merge conflicts detected",
            service="neo4j_provenance"
        )

        # API metrics
        self.register_metric(
            "api_request_count",
            MetricType.COUNTER,
            "Total API requests",
            service="api"
        )

        self.register_metric(
            "api_response_time_ms",
            MetricType.HISTOGRAM,
            "API response time",
            unit="ms",
            service="api"
        )

        self.register_metric(
            "api_error_rate",
            MetricType.GAUGE,
            "API error rate",
            unit="percentage",
            service="api"
        )

    def _initialize_default_alert_rules(self):
        """Initialize default alert rules based on performance targets"""

        # Vector retrieval SLA
        self.add_alert_rule(
            "vector_retrieval_sla_breach",
            "vector_retrieval_latency_ms",
            "memory_retrieval",
            "gt",
            self.performance_targets['vector_retrieval_p95_ms'],
            AlertSeverity.WARNING,
            "Vector retrieval p95 latency ({current_value:.1f}ms) exceeds target ({threshold}ms)"
        )

        # End-to-end performance
        self.add_alert_rule(
            "end_to_end_sla_breach",
            "expert_prediction_latency_ms",
            "expert_prediction",
            "gt",
            self.performance_targets['end_to_end_p95_ms'],
            AlertSeverity.ERROR,
            "End-to-end prediction latency ({current_value:.1f}ms) exceeds target ({threshold}ms)"
        )

        # Council projection performance
        self.add_alert_rule(
            "council_projection_sla_breach",
            "coherence_projection_latency_ms",
            "coherence_projection",
            "gt",
            self.performance_targets['council_projection_p95_ms'],
            AlertSeverity.WARNING,
            "Council projection latency ({current_value:.1f}ms) exceeds target ({threshold}ms)"
        )

        # Schema validation quality
        self.add_alert_rule(
            "schema_pass_rate_low",
            "schema_validation_pass_rate",
            "expert_prediction",
            "lt",
            self.performance_targets['schema_pass_rate'] * 100,
            AlertSeverity.ERROR,
            "Schema validation pass rate ({current_value:.1f}%) below target ({threshold}%)"
        )

        # Critic/repair loops efficiency
        self.add_alert_rule(
            "critic_repair_loops_high",
            "critic_repair_loops",
            "expert_prediction",
            "gt",
            self.performance_targets['critic_repair_loops_avg'],
            AlertSeverity.WARNING,
            "Average critic/repair loops ({current_value:.2f}) exceeds target ({threshold})"
        )

        # High error rates
        self.add_alert_rule(
            "api_error_rate_high",
            "api_error_rate",
            "api",
            "gt",
            5.0,  # 5% error rate threshold
            AlertSeverity.ERROR,
            "API error rate ({current_value:.1f}%) is high"
        )

        # Neo4j performance
        self.add_alert_rule(
            "neo4j_write_latency_high",
            "neo4j_write_latency_ms",
            "neo4j_provenance",
            "gt",
            1000,  # 1 second threshold
            AlertSeverity.WARNING,
            "Neo4j write latency ({current_value:.1f}ms) is high"
        )

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: str,
        unit: str = "",
        service: str = ""
    ) -> bool:
        """Register a new metric"""

        try:
            with self.lock:
                if name in self.metrics:
                    logger.warning(f"Metric {name} already exists, updating description")

                self.metrics[name] = Metric(
                    name=name,
                    metric_type=metric_type,
                    description=description,
                    unit=unit,
                    service=service
                )

                logger.debug(f"Registered metric: {name} ({metric_type.value})")
                return True

        except Exception as e:
            logger.error(f"Failed to register metric {name}: {e}")
            return False

    def record_metric(
        self,
        name: str,
        value: Union[float, int],
        tags: Dict[str, str] = None
    ) -> bool:
        """Record a metric value"""

        try:
            with self.lock:
                if name not in self.metrics:
                    logger.warning(f"Metric {name} not registered, auto-registering as gauge")
                    self.register_metric(name, MetricType.GAUGE, f"Auto-registered metric: {name}")

                metric = self.metrics[name]
                metric.add_point(value, tags)

                # Trigger alert evaluation for this metric
                self._evaluate_alerts_for_metric(name, float(value))

                return True

        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
            return False

    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None) -> bool:
        """Record a timer metric (convenience method)"""
        return self.record_metric(name, duration_ms, tags)

    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None) -> bool:
        """Increment a counter metric"""

        try:
            with self.lock:
                if name not in self.metrics:
                    self.register_metric(name, MetricType.COUNTER, f"Auto-registered counter: {name}")

                metric = self.metrics[name]
                current = metric.current_value or 0
                new_value = current + value

                return self.record_metric(name, new_value, tags)

        except Exception as e:
            logger.error(f"Failed to increment counter {name}: {e}")
            return False

    def set_gauge(self, name: str, value: Union[float, int], tags: Dict[str, str] = None) -> bool:
        """Set a gauge metric value"""
        return self.record_metric(name, value, tags)
    def add_alert_rule(
        self,
        rule_id: str,
        metric_name: str,
        service: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        message_template: str,
        evaluation_window_minutes: int = 5,
  pass      t:
          excepdown()
  hut.s    self
           try:
   "ion""n destructup o""Clean      "(self):
   __del__def

   )plete"tdown comrvice shutoringSenceMoniPerformar.info("ogge
        le)
        wn(wait=Falsor.shutdoelf.execut s       :
    tor')xecur(self, 'e hasatt if
         =5)
      in(timeout_thread.joound.backgrelf          sad'):
  round_threelf, 'backgttr(sf hasa   i
        alse
 g_active = Fmonitorin      self.

        ervice")ingStorformanceMoniown Perhutting d"Sgger.info( lo

vice"""itoring serdown the mon  """Shutf):
      down(sel  def shut
   return []

        e}")ve alerts: {et actiailed to gror(f"F  logger.er   e:
       ception as cept Ex     ex

          erts return al
                  )
       e=Truerevers, gered_at)igtreverity], a.rder[a.severity_o: (slambda akey=sort(  alerts.

     }           3
    O: erity.INFrtSev  Ale
   NG: 2,WARNIrtSeverity.        Ale       R: 1,
     .ERROertSeverity        Al            L: 0,
y.CRITICAveritSe   Alert               {
  _order = severity                timestamp
 and verity# Sort by se

  y]everitty == severiif alert.ss ertn al for alert is = [alertert        al
       ty:   if severi
       ]
       e == service.servicrts if alertn ale for alert ilertts = [a  aler             ice:
     rvf se      i
             ve]
   _actiif alert.is() esrts.valuin self.aler alert  forts = [alert   ale      ck:
       th self.lo          witry:


  """l filteringoptionaalerts with ve  acti"""Get       :
 st[Alert]Li= None) -> y veritSeity: Alert None, severrvice: str =ts(self, se_active_aler    def get
se
 urn Fal     ret")
       e}lert_id}: {{alert lve aed to resoror(f"Failr.erge  log
 tion as e:Excep  except
          rue
     urn T ret             ed")
  t_id} resolvalerrt {(f"Alenfologger.i

     utcnow()atetime. desolved_at =ert.r         ale
       e = Falss_activert.i        al
        _id]erts[alertt = self.aller   a
 e
        n Fals      retur              alerts:
lf.d not in selert_i a          if:
      self.lockith       w      ry:
     t

      alert"""lve an   """Reso   bool:
    r) ->ert_id: stf, ale_alert(sellvf reso  de
  n False
       reture}")
     d}: {rt_ialert {aledge led to acknow"Faile.error(f logger
       e:xception as pt E  exce
                  ue
    turn Tr  re            t}")
  ledgmenknowged_by}: {ac{acknowlededged by acknowl {alert_id} "Alertgger.info(f   lo
       now()
     .utc= datetimedged_at cknowlealert.a
          _bywledged = acknoed_bydgcknowle   alert.a             ment
acknowledgledgment = alert.acknow               rt_id]
 alerts[let = self.a     aler

          turn False         re
           .alerts: not in selfert_id     if al          k:
 elf.loc    with s
        y:
        tr
     rt"""edge an aleknowl    """Acl:
    boo: str) -> ed_byledgacknow str, ment:, acknowledgstr: _idself, alertlert(knowledge_a   def ac
 e)}
 ror': str(er  return {'         ")
  {e}summary:erformance  pailed to get(f"Fror  logger.er          on as e:
t Excepti  excep
               mmary
   turn su     re
                    as, 1)
    total_sllas / max(mpliant_s= coliance'] l_sla_compalvermmary['o     su        '])
   a_complianceummary['sl= len(s total_slas                t)
plianues() if com].valompliance'ry['sla_cummapliant in sm(1 for comsuslas = t_   complian            mpliance
 SLA co  # Overall
)
       uality"rediction qve initial poops: impro lepair/rduce criticRe].append("ns'ationdmme'recosummary[                       ']:
 ops_avgair_loeps['critic_retormance_targlf.perfoops > se   if avg_l
         vg']
      air_loops_aic_reprgets['crit_taceforman.per selfavg_loops <=pair'] = itic_reiance']['crcompl'sla_ry[umma         s       ops
    ] = avg_lo_loops_avg'ic_repairnce']['critrforma_peentmary['curr    sum
       .avg_valueritic_metric_loops = cvg        a           e:
 Nons not _value i_metric.avgicnd critic_metric ait       if cr        ps')
 c_repair_loo('criti.getetrics = self.mritic_metric c          s
     ir loopitic/repaCheck cr #
          sms")
     mechani repairdd and aneering prompt engiion: reviewma validat sche("Improveons'].appendendati'recomm    summary[
     s_rate']:a_pashemscs['ettargance_self.performass_rate <  if p
                   ate']
  ma_pass_r'schee_targets[manc self.perfors_rate >== pas'] validation'schema_e'][ncplia'sla_comry[ma         sum          ass_rate
 '] = ps_ratema_pas['scheance']erformt_p['currenmmary      su
     ue / 100current_val_metric.hemaate = sc     pass_r               t None:
e is nont_valumetric.curreschema_tric and if schema_me         ')
       rates_asalidation_pema_vs.get('schetricf.mtric = sel_meemasch             te
   s ra paschema s  # Check
                 ")
     K parametereduce  and rNSW indexes check Hretrieval:tor e veciz("Optimns'].appendendatioary['recomm       summ
   _p95_ms']:_retrievalors['vect_targetnce.performalf> sep95 if
                  ]
   eval_p95_ms'ritor_retectargets['vperformance_self.95 <= '] = por_retrieval']['vectcelianompmary['sla_c       sum               = p95
  s'] _m95l_prievaret'vector_ce'][t_performanmary['curren    sum
   es) * 0.95)]t(len(valuvalues)[ined( p95 = sort                10:
       lues) >=  if len(va                 s]
  ric.pointector_metfor p in vue ues = [p.val  val
 ints:.po_metricand vectortor_metric vec    if           s')
  al_latency_m_retrievtorvectrics.get('= self.meor_metric vect            nce
    val performactor retrie # Check ve

                  }
        ions': []atnd    'recomme             e': {},
   iancpl 'sla_com                  {},
  mance':ent_perfor      'curr           copy(),
   ets.nce_targf.performa selrgets':      'ta          at(),
    soform().ime.utcnowp': datetistamime       't           ry = {
    summa            k:
  ith self.loc      w
      ry:
        t     """
   nst targetssummary agaiformance et per"""G   ny]:
      Dict[str, Ay(self) ->arormance_summef get_perf
    d")
    : {e}rvice_name} for {seent failed assessm"Healthger.error(fog           l:
 on as excepticept E      ex
          =issues)
 s, issuestuta srvice_name,(service_healthpdate_se      self.ulth
      rvice headate se# Up
    ADED)
   EGRtus.DStatus, Serviceus = max(staat   st               ")
      e:.1f}mscurrent_valuc.metri {cy:tenjection laHigh pro.append(f" issues
0:t_value > 15tric.currenmen' and ce_projectiorenohee == 'c_namservice       elif              GRADED)
us.DEiceStatServmax(status, tatus =     s                    f}ms")
e:.1rrent_valumetric.cuency: {eval latri retigh vectorf"H.append(uesss         i          0:
     value > 10urrent_c.cmetril' and trievamemory_reme == 'ervice_na s   if
       _value:current and metric.metric.namelatency' in       if '         latency
 r high eck fo       # Ch

        EGRADED)viceStatus.Datus, Sertus = max(st     sta                  )
 f}%".1e:ent_valucurr{metric.rate: rror ted elevand(f"Eppe issues.a                     e
  % error rat > 5:  # 5aluec.current_v metri     elif
         us.UNHEALTHYiceStat= Servus tat      s          )
        f}%"lue:.1c.current_varate: {metrigh error "Hi.append(fues     iss                or rate
   rr # 10% ealue > 10: ent_vic.curr   if metr
       ue:valic.current_nd metrname atric.rate' in mer_ 'erro     if   s:
        ric service_metric in     for mets
       or rategh err hi Check for        #
        THY
     .HEALiceStatustatus = Serv          s = []
        issues      ics
ent metrsed on rec ba assessmentthle heal   # Simp
                       return

 ics:ice_metr serv   if not
                  me)
   ervice_nace(scs_for_servimetri= self.get_ce_metrics     servi        try:

"
 ce"" servius for alth statAssess hea""     "
   : str):nameervice_(self, slth_service_hea_assess  def
  }")
 : {edate failedealth upervice hor(f"Sogger.err        l e:
    ception as   except Ex
         e)
        alth(servicrvice_heself._assess_se             es:
   ce in servicervi   for s      vice
   ach ser for e health Update        #

  e)ric.servicmetvices.add(    ser              ce:
      ervif metric.s  i
           values():rics.n self.metmetric i      for        lock:
   self.      with      etrics
 ces from ml servialt    # Collec
             t()
vices = se         sertry:


        ""rics"meted on basservices ll us for a health stat"Update""        f):
lth(seleae_h_service_all def _updat

   }"): {efaileda cleanup r(f"Dat logger.erro            e:
tion asept Exc       excep
               s")
      d alert olold_alerts)}n({le"Cleaned up .debug(ferogg    l
    d_alerts:if ol
              alert_id]
 lerts[  del self.a
 ts: old_alerd inor alert_i  f

          ]
         ime_t_at < cutofft.resolvedd alered_at anesolvrt.rive and aleert.is_actf not al          i    ()
      msrts.ite self.ale int_id, alertfor alerd   alert_i                 ts = [
  old_aler           iod
    ion perthan retents older ed alertolvp resClean u  #               axlen)
y deque mndled b(already haic points old metr up ean   # Cl      :
       h self.lock wit

 s'])ion_hour'retentonfig[.curs=selfdelta(honow() - timeetime.utc datff_time =      cuto   :
   ry
        t   "
    ""ved alertsand resolic data up old metran """Cle
        (self):_old_dataf _cleanup  de
      d")
 stoppeoringund monitrockg"Bagger.info(  lo
         error
 eep on # Short sleep(5)  sl      time.
          rror: {e}")toring eground moni"Backfogger.error(         l:
       n as ept Exceptioexce
                  )
  s']nderval_secon_intvaluatiort_eg['aleonfif.c.sleep(sel      time   e
       il next cycl Sleep unt #
            )
     lth(hearvice__seate_all   self._upd            metrics
 h based on vice healter # Update s
            )
   ta(up_old_daclean._       self
  d data up ol    # Clean        y:
     tr
           ing_active:nitorf.moe sel   whil
            )
arted"onitoring stround mkg"Bacnfo(.iogger     l
   """
   g threadd monitorin"Backgroun  ""
    self):toring(_moniund _backgro
    def")
    {e}}:_nameiceor {servcs frvice metripdate seo ud tror(f"Faile logger.er           :
ion as ept Except      exce
        100
      l_checks) * totacks) /heiled_cs - fa_checkal ((totercentage =th.uptime_palhe                s > 0:
checktotal_     if
                 s)
health_checken(health. = lotal_checks t        heck)
   t cif nos.values() ecklth_chhealth.heak in (1 for checs = sumckfailed_che
   ime)ck over tld trantation wou implemerealin ified - simpl (meptilate ucu  # Cal
                     _times)
 ean(response.mics= statistme_ms onse_tih.avg_resp  healt          es:
    _timseon   if resp

 ) * 100total_countount / rror_c= (eate _rlth.error       hea
   _count > 0:al   if tot    trics
     ealth me h# Update

      ints])in metric.poor p value ftend([p.es.exesponse_tim r                 nts:
      poiif metric.                  lower():
  me.ric.nan met'latency' i() or owerc.name.letri_time' in mresponsef '   eli         or 0
     valueent_ric.currunt += met_co       total
     ower():ic.name.letrin mor 'count' e.lower() tric.nam' in mequest  elif 're           ue or 0
   valrent_ic.cur metrror_count +=     er
       lower():e.ric.nam metf 'error' in  i         cs:
     api_metri in or metric   f
          []
     nse_times =   respo     0
      =ntal_cou         tot 0
   ount =   error_c
             e]
   amce_nservi.service == () if mrics.values in self.met mics = [m fortr      api_me    cs
  t API metrifrom recenerror rate alculate  C      #try:


    """vice healths from served metricriUpdate de""        "eHealth):
Servic health: tr,name: se_elf, servics(se_metrice_servicef _updat
    d }")
   : {ervice_name} for {see healthvicpdate sero uailed terror(f"F    logger.:
        tion as e Excepexcept
                   alth)
   , hee_name(service_metricsrvicte_se  self._upda           metrics
   rived  de Update #
          s
  sues = issuerent_islth.cur       hea          ues:
   issf  i

   h_checks)e(healthecks.updatth.health_c   heal              ks:
   ealth_chec  if h
               utcnow()
  = datetime..last_check th      heal        tatus
  status = s   health.         ame]
    [service_nhealthelf.service_lth = shea

         )
        e.utcnow()eck=datetim    last_ch               ,
     tatus=status         s
       e,service_name_name=     servic              th(
     erviceHeal Se] =namce_rvilth[service_healf.se          se         lth:
 ce_heaservinot in self.ervice_name if s              :
  f.lock sel   with              try:


  "" status"alth service he"Update   ""
one
    ): = N: List[str]      issues
  l] = None,r, boo[stks: Dict health_chec      atus,
 ceSttatus: Servi       s
 str,name: rvice_se           self,
h(
     ervice_healtef update_s
    d}
   e)str(r': turn {'erro      re      )
{e}"oard data: ashb get diled tor(f"Faerro  logger.          s e:
n aept Exceptio        exc
       ta
      ashboard_da    return d
        ict()
    lth.to_d] = heaervice_name[se_health']'servicata[ashboard_d         d           :
    service == mevice_na.serlthearvice or h if not se            ():
       itemsice_health. self.servlth ine_name, heaicrv     for se  h
         ltice hea serv       # Add
                _dict()
   .tortrt_id] = aleale'][alert.['alertshboard_data        das           :
 ive_alertsactrt in for ale
 e]t.is_activ aleralues() iflf.alerts.vn set irt for aler [ale_alerts =ve    acti            erts
ive ald act# Ad

     c_datae] = metrietric.nams'][metric_data['mboard    dash

           * 0.99)]lues)d_vaorten(sues[int(le= sorted_val'p99'] c_data[   metri
     .95)] * 0alues)(sorted_vt(lenlues[ind_va sorte'] =95ta['ptric_da        me                    )]
 * 0.5rted_values)en(so(lvalues[intd_ sorte0'] =_data['p5ric         met
   ed(values)ues = sortrted_val so                   :
        alues) >= 10nd len(vOGRAM aricType.HIST == Metetric_typeric.m   if met                   ams
   for histogrntilesce   # Add per
                                    }

           points Last 50 #ints[-50:]] in recent_pofor p .to_dict() 'points': [p                          s),
  ntent_poirec': len(data_points  '
    e None,els if values es)cs.mean(valutatistiue': s'avg_val
     e, Nonlseif values eues)  max(valax_value':          'm
           else None,valuesalues) if e': min(vvalu    'min_                      e,
  alurent_vtric.cur': merrent_value    'cu                   ,
     ervicee': metric.sservic  '                      ,
    metric.unit   'unit':                   ,
       iption.descr': metricription    'desc                     value,
   _type.ric.metric'type': met
     tric.name,me': mena         '                   = {
 ric_data       met

          ent_points]n rec p ialue for= [p.v     values             ts:
       inrecent_po         if
            ]

       ff_timetamp >= cutoesimp.t    if                     s
etric.point p in mfor    p                 s = [
    int  recent_po                e range
  by timlter points # Fi             :
        in metricsfor metric               ric data
 met    # Add
           }
                       }
             LTHY])
   eStatus.HEA == Servic if s.statusth.values()heal.service_lf ses inor ': len([s fcesealthy_servi 'h
          ve]),.is_actialues() if arts.v self.aler a ina fo: len([tive_alerts'       'ac
           etrics),rics': len(mtal_metto         '               mmary': {
     'su            ts,
   targeformance_: self.pertargets'ance_form    'per               ': {},
 lthervice_hea 's                  ,
 s': {} 'alert                {},
    ics': 'metr                  ,
  service'service':
          minutes, time_range_s':minutege_me_ran      'ti        ,
      ormat()isof.utcnow().: datetimeimestamp'   't             = {
     hboard_data        das
                       alues())
 etrics.vself.m = list(rics met
             else:
   service)ervice(rics_for_sget_metelf.= srics        met
        ce:vi     if ser            specified
ifice  by servr metrics   # Filte
            utes)
     ge_mine_rans=timinuteedelta(m- tim() e.utcnowdatetimff_time =   cuto              self.lock:
ith           w try:

   "
  lization""r visuaoard data fo"Get dashb""
        tr, Any]:t[s-> Dic60) tes: int = e_minume_rang None, tice: str =, servielfrd_data(sshboaef get_da
    d
  service]service == f metric.ues() i.metrics.vallfn seetric ifor m[metric    return          lock:
with self.        ""
ce"servirics for a all metGet ""       "[Metric]:
 iste: str) -> Lf, service(sel_servictrics_for_me def get
   (name)
   s.getself.metricurn         ret:
    locklf.se  with ""
      "ric by namemet""Get a    "    c]:
 al[Metri-> Optionme: str) self, naric(get_met   def
 ")
 ion: {e}ficat noti alerted to send"Fail(forgger.err         loe:
   as xception cept E ex
                   here
      etc.k, Discord,ail, Slacld add em Cou       #
                 }")
  nt=2)load, indehook_payon.dumps(webjs_url']}: {['webhooklf.configbhook to {sed send wefo(f"Woulr.in       logge           }

     system'ng_etticouncil_bexpert_rce': '       'sou
   ormat(),().isofutcnow': datetime.tamp   'times
      ct(),alert.to_di   'alert':                     oad = {
 ylhook_pa         web
       questTTP red make an His wouln, thentatioal implem# In a re                    ):
rl'k_uoog.get('webhlf.confiand sewebhook' == 'nnel lif cha    e
           ge}")
   messae}: {alert.ic {alert.serv.upper()}]ty.value.severirt"ALERT [{ale(fninglogger.war                  og':
  l == 'lf channe i          s:
     n channelor channel i        f

         ['log'])nels', ('alert_chanfig.get = self.conannels ch  :

        try
        """elsnnnfigured chahrough coon ttificatialert no""Send
        "ert):Alalert: , ation(selft_notificerend_al _s
    def
  ") alert: {e}o triggerFailed tr(f"rro.e     logger e:
       Exception ascept    ex
                 }")
agelert.messered: {arigg"Alert t.warning(fger      log
alert)
   fication(lert_notind_aself._se         tions
   t notificaerSend al    #
 )
     tcnow( datetime.ured =_trigge  rule.last          e
e rule stat  # Updat
  ert
     d] = al.alert_irtrts[ale self.ale        lert
    # Store a
                )
            lue
   e=current_vaalurrent_v      cu        reshold,
  .thlue=ruleshold_va   thre               ),

        reshold=rule.thhold    thres            value,
    current_nt_value=  curre                  (
late.formatemple.message_tru message=
     le.severity,ty=ruseveri
    le.service,ruce=     servi
   etric_name,e.mrulname=tric_     me           .uuid4()),
idstr(uuid=t_aler            t(
    erert = Al    alt
        eate aler      # Crry:
          t
    "
  rt""r an ale"Trigge      "" float):
  value:, current_Rulert, rule: Aleelft(salerigger__tref     d

}: {e}")ame_nfor {metricon failed  evaluatiert.error(f"Algerlog             e:
ion as Exceptexcept
               )
    valuerent_rt(rule, curr_aleriggeself._t                 :
   ts)ta_point_value, da(currener_triggshould if rule.
             c.points)
 etrilen(ms = a_point   dat

    continue
    metric:    if not        )
    c_nameget(metrimetrics.tric = self.    me   :
         rulesevant_ule in rel    for r
            ]
             tric_name
c_name == mele.metri     if ru
   alues()s.vrt_ruleself.aleor rule in     rule f
    rules = [relevant_         etric
   s for this mruleFind alert  #              try:

        turn
    re        :
    ting']er'enable_alg[t self.confi      if no
          ic"""
ific metrfor a specrules e alert valuat"""E    t):
    alue: floa_vntcurreame: str, c_nmetrielf, metric(salerts_for_uate_def _eval
    rn False
    retu       ")
   }: {e}e_idule {rul add alert riled torror(f"Fa  logger.e          n as e:
 Exceptio   except
                   True
         return       }")
   namemetric__id} for {ulet rule: {rAdded alerinfo(f"er.        loggle
         = ruid][rule_lesru self.alert_
                   )
      s
    inuteoldown_mtes=coooldown_minu          c
          ow_minutes,ation_windlu_minutes=evan_windowio   evaluat         e,
        age_templatate=messge_templ    messa
         y,everitverity=s         se       old,
    ld=threshho   thres                dition,
 ndition=con       co           vice,
  vice=ser  ser                 c_name,
 _name=metri metric
     =rule_id,_id  rule
    tRule(le = Aler         ru      :
  self.lock      with
              try:
    """
     alert rule an"Add     ""> bool:
    15
    ) -s: int =own_minute    coold

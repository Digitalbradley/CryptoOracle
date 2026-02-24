import TopBar from './TopBar';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';
import StatusBar from './StatusBar';
import ConfluenceCard from './cards/ConfluenceCard';
import PriceCard from './cards/PriceCard';
import TACard from './cards/TACard';
import CelestialCard from './cards/CelestialCard';
import NumerologyCard from './cards/NumerologyCard';
import SentimentCard from './cards/SentimentCard';
import OnchainCard from './cards/OnchainCard';
import PoliticalCard from './cards/PoliticalCard';
import MacroCard from './cards/MacroCard';
import AlertsCard from './cards/AlertsCard';
import InterpretationCard from './cards/InterpretationCard';
import ChartCard from './cards/ChartCard';

export default function DashboardLayout() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-void)' }}>
      <div className="starfield" />

      {/* Desktop sidebar — hidden on mobile */}
      <Sidebar className="hidden lg:flex" />

      {/* Main area — offset by sidebar on desktop */}
      <div className="lg:ml-14 relative z-10">
        <TopBar />

        {/* Card grid */}
        <main className="px-3 pb-20 lg:pb-4 lg:px-4 pt-3">
          <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-5 gap-3 lg:gap-4">
            {/* Left column (3/5 on desktop) */}
            <div className="lg:col-span-3 space-y-3 lg:space-y-4">
              <PriceCard />
              <ChartCard />
              <TACard />
              <AlertsCard />
              <InterpretationCard />
            </div>

            {/* Right column (2/5 on desktop) */}
            <div className="lg:col-span-2 space-y-3 lg:space-y-4">
              <ConfluenceCard />
              <MacroCard />
              <CelestialCard />
              <NumerologyCard />
              <PoliticalCard />
              <SentimentCard />
              <OnchainCard />
            </div>
          </div>
        </main>

        {/* Desktop status bar */}
        <StatusBar className="hidden lg:flex" />
      </div>

      {/* Mobile bottom nav — hidden on desktop */}
      <BottomNav className="lg:hidden" />
    </div>
  );
}

"""Unit tests for period comparisons in CDS statistics."""

from datetime import date
from src.api.models.cds import PeriodComparison, CDSStatisticsData


class TestPeriodComparisonModels:
    """Test period comparison data models."""

    def test_period_comparison_with_data(self):
        """Test PeriodComparison model with available data."""
        comparison = PeriodComparison(
            period="1 month",
            days=30,
            start_date=date(2025, 10, 20),
            end_date=date(2025, 11, 20),
            start_value=0.0234,
            end_value=0.0245,
            absolute_change=0.0011,
            percentage_change=4.70,
            available=True,
        )

        assert comparison.period == "1 month"
        assert comparison.days == 30
        assert comparison.available is True
        assert comparison.absolute_change == 0.0011
        assert comparison.percentage_change == 4.70

    def test_period_comparison_without_data(self):
        """Test PeriodComparison model when data is not available."""
        comparison = PeriodComparison(
            period="52 weeks",
            days=364,
            start_date=None,
            end_date=date(2025, 11, 20),
            start_value=None,
            end_value=0.0245,
            absolute_change=None,
            percentage_change=None,
            available=False,
        )

        assert comparison.period == "52 weeks"
        assert comparison.available is False
        assert comparison.start_value is None
        assert comparison.absolute_change is None

    def test_statistics_data_with_comparisons(self):
        """Test CDSStatisticsData with period comparisons."""
        comparisons = [
            PeriodComparison(
                period="1 month",
                days=30,
                start_date=date(2025, 10, 20),
                end_date=date(2025, 11, 20),
                start_value=0.0234,
                end_value=0.0245,
                absolute_change=0.0011,
                percentage_change=4.70,
                available=True,
            ),
            PeriodComparison(
                period="3 months",
                days=90,
                start_date=date(2025, 8, 20),
                end_date=date(2025, 11, 20),
                start_value=0.0220,
                end_value=0.0245,
                absolute_change=0.0025,
                percentage_change=11.36,
                available=True,
            ),
        ]

        stats = CDSStatisticsData(
            total_records=100,
            earliest_date=date(2024, 1, 1),
            latest_date=date(2025, 11, 20),
            sources=["investing.com"],
            period_comparisons=comparisons,
        )

        assert stats.total_records == 100
        assert stats.period_comparisons is not None
        assert len(stats.period_comparisons) == 2
        assert stats.period_comparisons[0].period == "1 month"
        assert stats.period_comparisons[1].period == "3 months"

    def test_statistics_data_without_comparisons(self):
        """Test CDSStatisticsData without period comparisons."""
        stats = CDSStatisticsData(
            total_records=50,
            earliest_date=date(2024, 1, 1),
            latest_date=date(2025, 11, 20),
            sources=["investing.com"],
            period_comparisons=None,
        )

        assert stats.total_records == 50
        assert stats.period_comparisons is None

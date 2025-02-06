import numpy as np
import pytest

from jpx_derivatives.bsm import (
    d1,
    d2,
    delta_call,
    delta_put,
    gamma,
    implied_volatility_call,
    implied_volatility_put,
    price_call,
    price_put,
    theta_call,
    theta_put,
    vega,
)


@pytest.fixture
def option_params():
    """実際の市場データに基づくオプションパラメータを提供するフィクスチャ"""
    return {
        's': 38790.0,    # 株価
        'k': 38750.0,    # 行使価格
        't': 0.024657534246575342,  # 満期までの期間（年）
        'r': 0.001,      # 無リスク金利
        'sigma': 0.2087  # ボラティリティ (20.87%)
    }


def test_call_price(option_params):
    """コールオプション価格の計算が正しいことを確認"""
    call_price = price_call(**option_params)
    expected = 527.0
    assert abs(call_price - expected) < 1.0  # 1円未満の誤差を許容


def test_put_price(option_params):
    """プットオプション価格の計算が正しいことを確認"""
    put_price = price_put(**option_params)
    expected = 487.0
    assert abs(put_price - expected) < 1.0  # 1円未満の誤差を許容


def test_put_call_parity(option_params):
    """プットコールパリティが成り立つことを確認"""
    call_price = price_call(**option_params)
    put_price = price_put(**option_params)
    s, k, t, r = [option_params[key] for key in ['s', 'k', 't', 'r']]
    
    # C - P = S - K*e^(-rT)
    left_side = call_price - put_price
    right_side = s - k * np.exp(-r * t)
    assert abs(left_side - right_side) < 1.0  # 1円未満の誤差を許容


def test_vega_calculation(option_params):
    """ベガの計算が正しいことを確認"""
    vega_value = vega(**option_params)
    expected = 2426.32
    assert abs(vega_value - expected) < 1.0  # 1未満の誤差を許容


def test_delta_call_calculation(option_params):
    """コールオプションのデルタが正しいことを確認"""
    delta = delta_call(**option_params)
    expected = 0.5191
    assert abs(delta - expected) < 0.001  # 0.1%未満の誤差を許容


def test_delta_put_calculation(option_params):
    """プットオプションのデルタが正しいことを確認"""
    delta = delta_put(**option_params)
    expected = -0.4809
    assert abs(delta - expected) < 0.001  # 0.1%未満の誤差を許容


def test_gamma_calculation(option_params):
    """ガンマの計算が正しいことを確認"""
    gamma_value = gamma(**option_params)
    expected = 0.000314
    assert abs(gamma_value - expected) < 0.00001  # 0.001%未満の誤差を許容


def test_theta_call_calculation(option_params):
    """コールオプションのシータが正しいことを確認"""
    theta = theta_call(**option_params)
    expected = -10262.6685
    assert abs(theta - expected) < 365.0  # 1日あたり1未満の誤差を許容


def test_theta_put_calculation(option_params):
    """プットオプションのシータが正しいことを確認"""
    theta = theta_put(**option_params)
    expected = -10262.705
    assert abs(theta - expected) < 365.0  # 1日あたり1未満の誤差を許容


def test_implied_volatility_call(option_params):
    """コールオプションのインプライドボラティリティの計算が正しいことを確認"""
    params = {k: option_params[k] for k in ['s', 'k', 't', 'r']}
    impl_vol = implied_volatility_call(**params, price=527.0)
    expected = 0.2087  # 20.87%
    assert abs(impl_vol - expected) < 0.001  # 0.1%未満の誤差を許容


def test_implied_volatility_put(option_params):
    """プットオプションのインプライドボラティリティの計算が正しいことを確認"""
    params = {k: option_params[k] for k in ['s', 'k', 't', 'r']}
    impl_vol = implied_volatility_put(**params, price=487.0)
    expected = 0.2087  # 20.87%
    assert abs(impl_vol - expected) < 0.001  # 0.1%未満の誤差を許容


def test_zero_time_to_expiry(option_params):
    """満期時のオプション価値が正しいことを確認"""
    params = option_params.copy()
    params['t'] = 0.0
    
    # コールオプション
    call_value = price_call(**params)
    assert call_value == max(0, params['s'] - params['k'])
    
    # プットオプション
    put_value = price_put(**params)
    assert put_value == max(0, params['k'] - params['s']) 